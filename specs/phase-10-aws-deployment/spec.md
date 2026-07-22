# Phase 10 Specification: AWS Deployment

- **Status:** In Progress
- **Date:** 2026-07-22
- **Phase:** 10 of 10

## Problem

The platform runs locally in Docker Compose and is well-covered by tests, but
there is no production deployment path. The previous roadmap pointed at GCP,
which no longer matches the desired target cloud. We need an AWS deployment
plan that keeps the existing service boundaries and Postgres-backed design
intact without forcing a rewrite of the application layer.

## Scope

### Infrastructure

1. Provision AWS infrastructure with Terraform.
2. Run the four FastAPI services as separate containers on ECS Fargate.
3. Replace local Postgres with Amazon RDS for PostgreSQL and enable the
   `pgvector` extension as part of database bootstrap/migrations.
4. Store container images in Amazon ECR.
5. Expose public HTTP entrypoints through an Application Load Balancer.

### Runtime and operations

1. Configure per-service environment variables and secrets via AWS-native
   mechanisms (`Secrets Manager` / `SSM Parameter Store`).
2. Preserve the current port layout and health/readiness contract so service
   containers can be deployed without code-path forks.
3. Send logs to CloudWatch Logs.
4. Wire `RAG_OTEL_EXPORTER_ENDPOINT` to an AWS-hosted collector when
   observability is enabled.

### Delivery workflow

1. Build and push service images through CI.
2. Run Alembic migrations before or during deployment from the ingestion
   service lineage.
3. Document environment setup, deploy steps, rollback basics, and required AWS
   resources.

## Out of scope

- Replacing Bedrock with another provider or changing the provider abstraction.
- Re-architecting services into Lambda functions.
- Multi-region failover or autoscaling policies beyond sensible MVP defaults.
- Full VPC hardening, WAF, SSO, and enterprise IAM design.

## Proposed target architecture

- `ingestion`, `processing`, `retrieval`, and `generation` run as independent
  ECS services on Fargate.
- `processing` runs continuously with `worker_enabled=true` and no public
  ingress beyond health endpoints if internal-only routing is chosen.
- One RDS PostgreSQL instance backs all services, consistent with ADR-0004.
- One ALB fronts the public API surface; routing may expose all services
  directly or only the externally needed ones.
- ECR stores versioned images for each service.
- CloudWatch Logs captures container logs; OpenTelemetry export is optional.

## Testing

- Terraform validation and formatting checks in CI.
- Container build verification for all services.
- Smoke deployment verification:
  - ALB-reachable `/health` endpoints return 200 for public services.
  - Ingestion migrations succeed against RDS.
  - End-to-end ingest -> process -> retrieve -> generate works in a deployed
    environment with real secrets configured.

## Acceptance Criteria

- [ ] A Phase 10 Terraform stack exists for AWS infrastructure.
- [ ] Each service can be built, published to ECR, and deployed on ECS Fargate.
- [ ] RDS PostgreSQL is reachable by all services and supports `pgvector`.
- [ ] Secrets and config are managed outside the repo.
- [ ] Deployment documentation is sufficient for a fresh environment bootstrap.
- [ ] A deployed environment can answer a real RAG query end to end.
