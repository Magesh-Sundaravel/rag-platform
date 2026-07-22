resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-db"
  subnet_ids = var.subnet_ids
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.name_prefix}-postgres16"
  family = "postgres16"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }
}

resource "aws_db_instance" "this" {
  identifier                 = "${var.name_prefix}-postgres"
  engine                     = "postgres"
  engine_version             = "16.4"
  instance_class             = var.instance_class
  allocated_storage          = var.allocated_storage
  storage_type               = "gp3"
  username                   = var.db_username
  password                   = var.db_password
  db_name                    = var.db_name
  port                       = 5432
  publicly_accessible        = false
  multi_az                   = false
  skip_final_snapshot        = true
  deletion_protection        = false
  backup_retention_period    = 7
  auto_minor_version_upgrade = true
  db_subnet_group_name       = aws_db_subnet_group.this.name
  vpc_security_group_ids     = var.security_group_ids
  parameter_group_name       = aws_db_parameter_group.this.name
}
