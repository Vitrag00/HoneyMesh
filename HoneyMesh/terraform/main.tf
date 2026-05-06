terraform {
  required_version = ">= 1.0"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# Resolve the project root (one level above this terraform/ directory)
locals {
  project_root = "${path.module}/.."
}

# Create log directory structure for all honeypot services
resource "null_resource" "create_log_dirs" {
  provisioner "local-exec" {
    command = <<-EOT
      mkdir -p "${local.project_root}/honeypots/logs/cowrie"
      mkdir -p "${local.project_root}/honeypots/logs/dionaea"
      mkdir -p "${local.project_root}/honeypots/logs/dashboard"
    EOT
  }

  triggers = {
    always_run = timestamp()
  }
}

# Generate Ansible inventory file dynamically
resource "local_file" "ansible_inventory" {
  filename = "${local.project_root}/ansible/inventory.ini"
  content  = <<-EOT
    [honeymesh]
    localhost ansible_connection=local
  EOT

  depends_on = [null_resource.create_log_dirs]
}

# Start all HoneyMesh services via docker-compose
resource "null_resource" "deploy_honeymesh" {
  provisioner "local-exec" {
    command     = "docker compose up -d"
    working_dir = "${local.project_root}/honeypots"
  }

  depends_on = [
    null_resource.create_log_dirs,
    local_file.ansible_inventory,
  ]

  triggers = {
    compose_hash = filemd5("${local.project_root}/honeypots/docker-compose.yml")
  }
}

output "honeymesh_status" {
  description = "HoneyMesh service URLs"
  value = {
    ssh_honeypot = "localhost:2222"
    dashboard    = "http://localhost:5000"
    prometheus   = "http://localhost:9090"
    grafana      = "http://localhost:3000"
  }
}
