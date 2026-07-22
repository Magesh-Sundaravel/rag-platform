# Phase 10 Design

## Platform choices

- **Compute:** Amazon ECS on Fargate, one task definition per service.
- **Registry:** Amazon ECR, one repository per service.
- **Database:** Amazon RDS for PostgreSQL.
- **Ingress:** Application Load Balancer.
- **Secrets/config:** AWS Secrets Manager for secrets, SSM Parameter Store for
  non-secret shared config where useful.
- **Observability:** CloudWatch Logs by default; optional OTLP collector path
  for traces.

This keeps the deployment model close to local Docker images and avoids the
operational overhead of Kubernetes for the first production release.

## Service layout

### Public services

- `ingestion`
- `generation`

These sit behind the ALB and expose the existing HTTP APIs.

### Internal services

- `retrieval`
- `processing`

`generation` calls `retrieval` over private service discovery or internal ALB
routing. `processing` runs as a long-lived worker/API task and does not need
internet-facing exposure.

## Data and migrations

- Reuse the existing shared-database model from `libs/db`.
- Run ingestion Alembic migrations as the authoritative schema path during
  deploy.
- Ensure database bootstrap enables `vector`; if AWS-managed Postgres
  constraints make extension setup environment-specific, document that as an
  operator prerequisite.

## Terraform modules

Suggested layout:

```text
infra/aws/
  main.tf
  variables.tf
  outputs.tf
  modules/
    network/
    ecr/
    rds/
    ecs_service/
    alb/
```

Core resources:

- VPC with public/private subnets
- Security groups for ALB, ECS tasks, and RDS
- ECR repositories
- ECS cluster, task definitions, and services
- ALB listeners/target groups
- RDS PostgreSQL instance
- IAM roles for task execution and runtime access to secrets/logs

## CI/CD flow

1. Build service images from the existing Dockerfiles.
2. Tag images with commit SHA.
3. Push to ECR.
4. Apply Terraform for the target environment.
5. Run migrations.
6. Roll ECS services to the new image tags.

This can start as GitHub Actions with manual approval on production applies.

## App-level assumptions

- Existing health endpoints remain the deployment probes.
- `retrieval_url` in generation becomes an internal AWS service endpoint via
  env var configuration.
- No code changes are required to switch clouds, aside from deployment-time
  configuration and any provider credentials/secrets.
