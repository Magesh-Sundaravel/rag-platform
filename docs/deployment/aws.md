# AWS Deployment Runbook

This phase deploys the four-service RAG platform to AWS using Terraform, ECS
on Fargate, Amazon RDS for PostgreSQL, ECR, CloudWatch Logs, and a public ALB.

## Topology

- `ingestion` and `generation` are public ECS services behind one ALB.
- `processing` and `retrieval` are private ECS services discovered through
  Cloud Map DNS inside the VPC.
- One RDS PostgreSQL instance backs all services.
- One SQS queue (plus DLQ) carries ingestion → processing hand-off
  (ADR-0009).
- One ECR repository exists per service image.
- Logs go to CloudWatch; traces remain optional through
  `RAG_OTEL_EXPORTER_ENDPOINT`.

## Required AWS prerequisites

1. Create or choose an AWS account and enable Bedrock model access for:
   `amazon.titan-embed-text-v2:0` and `amazon.nova-micro-v1:0`.
2. Create a GitHub Actions deploy role that trusts your repository through OIDC.
3. Create these GitHub repository secrets:
   - `AWS_ACCOUNT_ID`
   - `AWS_DEPLOY_ROLE_ARN`
   - `RAG_DB_PASSWORD`
4. Decide how you will store runtime config:
   - Non-secret values can be passed through Terraform `service_environment`.
   - Secret values should be pre-created in Secrets Manager or SSM Parameter
     Store, then referenced by ARN in `service_secrets`.
   - Terraform creates the shared `RAG_DATABASE_URL` secret automatically from
     the provisioned RDS endpoint and the supplied database password.

## Runtime configuration by service

Shared values:

- `RAG_ENVIRONMENT=prod`
- `RAG_LOG_LEVEL=INFO`
- `RAG_OTEL_EXPORTER_ENDPOINT` only when a collector exists

`ingestion`

- `RAG_SERVICE_NAME=ingestion`
- `RAG_PORT=8001`
- `RAG_DATABASE_URL` from the Terraform-managed Secrets Manager secret
- `RAG_PROCESSING_QUEUE_URL` from the Terraform-managed SQS queue

`processing`

- `RAG_SERVICE_NAME=processing`
- `RAG_PORT=8002`
- `RAG_DATABASE_URL` from the Terraform-managed Secrets Manager secret
- `RAG_EMBEDDING_PROVIDER=bedrock`
- `RAG_WORKER_ENABLED=true`
- `RAG_PROCESSING_QUEUE_URL` from the Terraform-managed SQS queue
- `RAG_MAX_RECEIVE_COUNT=3` (must match the queue's redrive `maxReceiveCount`)
- `RAG_CHUNK_STRATEGY=recursive`
- `RAG_CHUNK_SIZE=1200`
- `RAG_CHUNK_OVERLAP=200`

`retrieval`

- `RAG_SERVICE_NAME=retrieval`
- `RAG_PORT=8003`
- `RAG_DATABASE_URL` from the Terraform-managed Secrets Manager secret
- `RAG_EMBEDDING_PROVIDER=bedrock`

`generation`

- `RAG_SERVICE_NAME=generation`
- `RAG_PORT=8004`
- `RAG_GENERATION_PROVIDER=bedrock`
- `RAG_RETRIEVAL_URL=http://retrieval.<cloudmap-namespace>:8003`
- `RAG_REQUEST_TIMEOUT_SECONDS=10.0`
- `RAG_RETRIEVAL_RETRIES=2`

AWS SDK / Bedrock auth:

- The ECS task role supplies Bedrock permissions.
- If your environment requires an explicit region env var, store `AWS_REGION`
  or `AWS_DEFAULT_REGION` in SSM and inject it through `service_secrets`.

## First-time infrastructure bootstrap

1. Copy [infra/aws/terraform.tfvars.example](../../infra/aws/terraform.tfvars.example)
   to a local `terraform.tfvars` file that is never committed.
2. Fill in `db_password` and any service-specific overrides.
3. Initialize and validate Terraform:

```bash
cd infra/aws
terraform init
terraform fmt -recursive
terraform validate
```

4. Create the infrastructure:

```bash
terraform apply
```

5. Record the outputs:
   - `alb_dns_name`
   - `cluster_name`
   - `database_endpoint`
   - `ecr_repository_urls`
   - `cloudmap_namespace`

## Image build and push

The GitHub Actions workflow `.github/workflows/aws-deploy.yml` builds and
pushes all four service images on manual dispatch. For a manual local push:

```bash
AWS_REGION=eu-west-1
AWS_ACCOUNT_ID=123456789012
TAG=$(git rev-parse HEAD)

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin \
    "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

for service in ingestion processing retrieval generation; do
  docker build -f "services/${service}/Dockerfile" -t \
    "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/rag-platform-prod-${service}:${TAG}" .
  docker push \
    "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/rag-platform-prod-${service}:${TAG}"
done
```

## Cutover from the Postgres job queue (ADR-0009)

Migration `0007` drops the `jobs` table without moving its rows to SQS. On an
environment that already runs the old images, drain the old queue first:

1. Stop new uploads: scale the `ingestion` service to 0 tasks.
2. Let the old `processing` tasks finish the backlog. Wait until this
   returns 0:

```sql
SELECT count(*) FROM jobs WHERE status IN ('pending', 'in_progress');
```

   Rows stuck in `in_progress` (from a crashed worker) never drain; note
   their documents and continue.
3. Run the migrations (next section), deploy the new images, and scale
   `ingestion` back up.
4. Any document still `pending` after cutover has no SQS message. Re-upload
   the same file: ingestion re-sends the message for a pending duplicate
   instead of returning 409. To list them:

```sql
SELECT id, filename FROM documents WHERE status = 'pending';
```

Fresh environments can skip this section.

## Database migrations and pgvector enablement

After the infrastructure exists, enable the `vector` extension once per
database, then run Alembic from the ingestion task definition lineage.

1. Connect to the RDS database as a privileged user and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2. Run migrations using the ingestion image. The Docker image now includes the
   Alembic directory and config so the task can run in ECS:

```bash
aws ecs run-task \
  --cluster <cluster-name> \
  --launch-type FARGATE \
  --task-definition <ingestion-task-definition-arn> \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-aaa,subnet-bbb],securityGroups=[sg-ecs],assignPublicIp=DISABLED}" \
  --overrides '{
    "containerOverrides": [{
      "name": "ingestion",
      "command": [
        "alembic",
        "-c",
        "/app/services/ingestion/alembic.ini",
        "upgrade",
        "head"
      ]
    }]
  }'
```

## Deployment flow

1. Dispatch `.github/workflows/aws-deploy.yml`.
2. Set `environment=prod`.
3. Leave `apply=false` for a safe plan-only run, or set `apply=true` to roll
   the deployment.
4. Confirm Terraform plans the new `service_image_tag`.
5. Apply and wait for all four ECS services to stabilize.

## Smoke tests

Once the deployment completes:

1. Confirm public health checks:

```bash
curl "http://<alb-dns-name>:8001/health"
curl "http://<alb-dns-name>:8004/health"
```

2. Ingest a document through the ALB-fronted ingestion service.
3. Wait for processing to complete.
4. Query generation:

```bash
curl -X POST "http://<alb-dns-name>:8004/query" \
  -H "content-type: application/json" \
  -d '{"question":"What does the uploaded document say?","top_k":4}'
```

5. Verify the response includes an answer and citations.

## Rollback

1. Redeploy the prior image tag by re-running Terraform with
   `-var service_image_tag=<older-sha>`.
2. If the failure is schema-related, roll the ECS services back first and only
   then consider a compensating migration.
3. Review CloudWatch Logs for the failed task set before deleting anything.
