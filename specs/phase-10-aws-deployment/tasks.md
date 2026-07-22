# Phase 10 Tasks

1. Create AWS deployment spec artifacts and align roadmap/status docs. -> verify: Phase 10 roadmap/status references point to AWS deployment.
2. Add Terraform scaffolding for AWS networking, ECR, ECS Fargate, ALB, and RDS. -> verify: `terraform fmt -check` and `terraform validate`.
3. Define runtime config/secrets strategy for all four services. -> verify: documented env and secret sources per service.
4. Add CI steps for image build/push and Terraform plan/apply workflow. -> verify: workflow file validates and references all four services.
5. Document migration, deployment, smoke-test, and rollback steps. -> verify: a fresh operator can deploy and hit `/health`.
