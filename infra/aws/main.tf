data "aws_availability_zones" "available" {
  state = "available"
}

module "network" {
  source = "./modules/network"

  name_prefix          = local.name_prefix
  vpc_cidr             = var.vpc_cidr
  availability_zones   = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

resource "aws_service_discovery_private_dns_namespace" "services" {
  name = local.cloudmap_namespace
  vpc  = module.network.vpc_id
}

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb"
  description = "Public ingress to the RAG ALB"
  vpc_id      = module.network.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "alb_ingress_generation" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8004
  to_port           = 8004
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "alb_ingress_ingestion" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8001
  to_port           = 8001
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "alb_egress_all" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_security_group" "ecs" {
  name        = "${local.name_prefix}-ecs"
  description = "Service tasks for the RAG platform"
  vpc_id      = module.network.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb_ingestion" {
  security_group_id            = aws_security_group.ecs.id
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8001
  to_port                      = 8001
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb_generation" {
  security_group_id            = aws_security_group.ecs.id
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8004
  to_port                      = 8004
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "ecs_internal" {
  security_group_id            = aws_security_group.ecs.id
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 0
  to_port                      = 65535
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "ecs_all" {
  security_group_id = aws_security_group.ecs.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds"
  description = "PostgreSQL for the RAG platform"
  vpc_id      = module.network.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_ecs" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "rds_all" {
  security_group_id = aws_security_group.rds.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

module "ecr" {
  source = "./modules/ecr"

  name_prefix = local.name_prefix
  repositories = {
    for service_name, config in local.services :
    service_name => config.image_repository
  }
}

module "alb" {
  source = "./modules/alb"

  name_prefix        = local.name_prefix
  vpc_id             = module.network.vpc_id
  public_subnet_ids  = module.network.public_subnet_ids
  security_group_ids = [aws_security_group.alb.id]
  public_services = {
    for service_name, config in local.services :
    service_name => {
      port         = config.port
      health_check = config.health_check
    }
    if config.public
  }
}

module "rds" {
  source = "./modules/rds"

  name_prefix         = local.name_prefix
  subnet_ids          = module.network.private_subnet_ids
  security_group_ids  = [aws_security_group.rds.id]
  db_name             = var.db_name
  db_username         = var.db_username
  db_password         = var.db_password
  instance_class      = var.db_instance_class
  allocated_storage   = var.db_allocated_storage
}

resource "aws_secretsmanager_secret" "database_url" {
  name = "${local.name_prefix}/database-url"
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = local.database_url
}

# Processing hand-off queue (ADR-0009). maxReceiveCount must match the
# processing service's RAG_MAX_RECEIVE_COUNT.
resource "aws_sqs_queue" "processing_dlq" {
  name                      = "${local.name_prefix}-processing-dlq"
  message_retention_seconds = 1209600
}

resource "aws_sqs_queue" "processing" {
  name                       = "${local.name_prefix}-processing"
  visibility_timeout_seconds = local.processing_visibility_timeout_seconds
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.processing_dlq.arn
    maxReceiveCount     = local.processing_max_receive_count
  })
}

resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"
}

resource "aws_iam_role" "ecs_execution" {
  name = "${local.name_prefix}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "${local.name_prefix}-ecs-execution-secrets"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "ssm:GetParameters",
        "ssm:GetParameter"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role" "ecs_task" {
  name = "${local.name_prefix}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_runtime" {
  name = "${local.name_prefix}-ecs-task-runtime"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:Converse",
          "bedrock:ConverseStream"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.processing.arn
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "ssm:GetParameters",
          "ssm:GetParameter"
        ]
        Resource = "*"
      }
    ]
  })
}

module "ecs_service" {
  source   = "./modules/ecs_service"
  for_each = local.services

  name_prefix                = local.name_prefix
  service_name               = each.key
  cluster_arn                = aws_ecs_cluster.main.arn
  subnet_ids                 = module.network.private_subnet_ids
  security_group_ids         = [aws_security_group.ecs.id]
  cloudmap_namespace_id      = aws_service_discovery_private_dns_namespace.services.id
  execution_role_arn         = aws_iam_role.ecs_execution.arn
  task_role_arn              = aws_iam_role.ecs_task.arn
  desired_count              = lookup(var.service_desired_count, each.key, 1)
  cpu                        = lookup(var.service_cpu, each.key, 512)
  memory                     = lookup(var.service_memory, each.key, 1024)
  container_port             = each.value.port
  image_uri                  = "${module.ecr.repository_urls[each.key]}:${lookup(var.service_image_tags, each.key, var.service_image_tag)}"
  environment                = merge(
    each.value.env,
    var.otel_exporter_endpoint == null ? {} : { RAG_OTEL_EXPORTER_ENDPOINT = var.otel_exporter_endpoint }
  )
  secrets                    = merge(
    { RAG_DATABASE_URL = aws_secretsmanager_secret.database_url.arn },
    lookup(var.service_secrets, each.key, {})
  )
  assign_public_ip           = false
  enable_service_discovery   = true
  target_group_arn           = try(module.alb.target_group_arns[each.key], null)
  aws_region                 = var.aws_region
}
