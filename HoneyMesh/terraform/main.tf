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

# Create log directory structure for all honeypot services
resource "null_resource" "create_log_dirs" {
  provisioner "local-exec" {
    command = <<-EOT
      mkdir -p honeypots/logs/cowrie
      mkdir -p honeypots/logs/dionaea
      mkdir -p honeypots/logs/dashboard
    EOT
    working_dir = path.module == "." ? path.root : "${path.root}"
  }

  triggers = {
    always_run = timestamp()
  }
}

# Generate Ansible inventory file dynamically
resource "local_file" "ansible_inventory" {
  filename = "${path.root}/ansible/inventory.ini"
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
    working_dir = "${path.root}/honeypots"
  }

  depends_on = [
    null_resource.create_log_dirs,
    local_file.ansible_inventory,
  ]

  triggers = {
    compose_hash = filemd5("${path.root}/honeypots/docker-compose.yml")
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
