locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Phase       = "10"
  }

  base_environment = {
    RAG_ENVIRONMENT = var.environment
    RAG_LOG_LEVEL   = "INFO"
  }

  cloudmap_namespace = "${var.environment}.${var.project_name}.local"

  services = {
    ingestion = {
      port             = 8001
      public           = true
      health_check     = "/health"
      container_name   = "ingestion"
      image_repository = "ingestion"
      env = merge(
        local.base_environment,
        {
          RAG_SERVICE_NAME = "ingestion"
          RAG_PORT         = "8001"
        },
        lookup(var.service_environment, "ingestion", {})
      )
    }
    processing = {
      port             = 8002
      public           = false
      health_check     = "/health"
      container_name   = "processing"
      image_repository = "processing"
      env = merge(
        local.base_environment,
        {
          RAG_SERVICE_NAME           = "processing"
          RAG_PORT                   = "8002"
          RAG_EMBEDDING_PROVIDER     = "bedrock"
          RAG_WORKER_ENABLED         = "true"
          RAG_POLL_INTERVAL_SECONDS  = "1.0"
          RAG_CHUNK_STRATEGY         = "recursive"
          RAG_CHUNK_SIZE             = "1200"
          RAG_CHUNK_OVERLAP          = "200"
        },
        lookup(var.service_environment, "processing", {})
      )
    }
    retrieval = {
      port             = 8003
      public           = false
      health_check     = "/health"
      container_name   = "retrieval"
      image_repository = "retrieval"
      env = merge(
        local.base_environment,
        {
          RAG_SERVICE_NAME       = "retrieval"
          RAG_PORT               = "8003"
          RAG_EMBEDDING_PROVIDER = "bedrock"
        },
        lookup(var.service_environment, "retrieval", {})
      )
    }
    generation = {
      port             = 8004
      public           = true
      health_check     = "/health"
      container_name   = "generation"
      image_repository = "generation"
      env = merge(
        local.base_environment,
        {
          RAG_SERVICE_NAME             = "generation"
          RAG_PORT                     = "8004"
          RAG_GENERATION_PROVIDER      = "bedrock"
          RAG_RETRIEVAL_URL            = "http://retrieval.${local.cloudmap_namespace}:8003"
          RAG_REQUEST_TIMEOUT_SECONDS  = "10.0"
          RAG_RETRIEVAL_RETRIES        = "2"
        },
        lookup(var.service_environment, "generation", {})
      )
    }
  }

  database_url = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${module.rds.endpoint}:5432/${var.db_name}"
}
