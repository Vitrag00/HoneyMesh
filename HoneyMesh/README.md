# HoneyMesh

A distributed honeypot cybersecurity platform with a complete DevOps pipeline running on Kali Linux.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HoneyMesh Platform                       │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │   Cowrie    │   │   Dionaea    │   │  Flask Dashboard     │ │
│  │  SSH :2222  │   │ Multi-proto  │   │     :5000            │ │
│  │  Honeypot   │   │  Honeypot    │   │  Attack Intel UI     │ │
│  └──────┬──────┘   └──────┬───────┘   └──────────┬───────────┘ │
│         │                 │                        │             │
│         └────────┬────────┘                        │             │
│                  │ logs/                           │ /metrics    │
│         ┌────────▼────────────────────────────────▼──────────┐  │
│         │              honeymesh-net (Docker bridge)          │  │
│         └────────────────────────┬───────────────────────────┘  │
│                                  │                               │
│              ┌───────────────────▼──────────────────┐           │
│              │            Prometheus :9090            │           │
│              │         (scrapes all services)         │           │
│              └───────────────────┬──────────────────┘           │
│                                  │                               │
│              ┌───────────────────▼──────────────────┐           │
│              │             Grafana :3000              │           │
│              │      HoneyMesh Attacker Intelligence   │           │
│              └──────────────────────────────────────┘           │
│                                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Jenkins  │  │   SonarQube  │  │  Ansible │  │ Terraform │  │
│  │  :8080   │  │    :9000     │  │  Deploy  │  │ Provision │  │
│  │ CI/CD    │  │ Code Quality │  │ Playbook │  │ main.tf   │  │
│  └──────────┘  └──────────────┘  └──────────┘  └───────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Kubernetes (k8s/) — optional scale-out         │ │
│  │   cowrie-deployment  |  dionaea-deployment  |  hpa.yml      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Kali Linux (or any Debian-based host)
- Docker + Docker Compose v2
- Terraform >= 1.0
- Ansible >= 2.14 with `community.docker` collection
- Jenkins with SonarQube Scanner plugin
- `sonar-scanner` CLI in PATH

```bash
# Install Ansible Docker collection
ansible-galaxy collection install community.docker

# Install sonar-scanner (example)
sudo snap install sonar-scanner --classic
```

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Vitrag00/HoneyMesh.git
cd HoneyMesh

# 2. Provision infrastructure and start services
terraform -chdir=terraform init
terraform -chdir=terraform apply -auto-approve

# 3. Access services
```

| Service          | URL                     |
|------------------|-------------------------|
| SSH Honeypot     | `localhost:2222`        |
| Dashboard        | http://localhost:5000   |
| Prometheus       | http://localhost:9090   |
| Grafana          | http://localhost:3000   |
| Jenkins          | http://localhost:8080   |
| SonarQube        | http://localhost:9000   |

Grafana default credentials: `admin / honeymesh`

## Lab Mapping

| Component                       | File(s)                              | Lab Covered          |
|---------------------------------|--------------------------------------|----------------------|
| Docker honeypot containers      | `honeypots/*/Dockerfile`             | Lab 2 — Docker       |
| Docker Compose orchestration    | `honeypots/docker-compose.yml`       | Lab 2 — Docker       |
| Kubernetes deployments + HPA    | `k8s/*.yml`                          | Lab 3 — Kubernetes   |
| Git version control             | `.git/` + `README.md`                | Lab 4 — Git          |
| Jenkins CI/CD pipeline          | `jenkins/Jenkinsfile`                | Lab 5 — Jenkins      |
| SonarQube static analysis       | `sonarqube/sonar-project.properties` | Lab 8 — SonarQube    |
| Ansible configuration mgmt      | `ansible/playbook.yml`               | Lab 9 — Ansible      |
| Prometheus + Grafana monitoring | `monitoring/`                        | Lab 9 — Monitoring   |
| Terraform IaC provisioning      | `terraform/main.tf`                  | Lab 10 — Terraform   |

## Demo Script

```bash
# Start all services
terraform -chdir=terraform apply -auto-approve

# Simulate an SSH attack against cowrie (from another terminal)
ssh -p 2222 root@localhost          # try password: 123456

# Watch live in the dashboard
open http://localhost:5000

# Check Prometheus metrics
curl http://localhost:5000/metrics

# Check Grafana (import monitoring/grafana-dashboard.json manually)
open http://localhost:3000

# Run full CI/CD pipeline
# → Open Jenkins at http://localhost:8080, create a pipeline job,
#   point it to Jenkinsfile, and click Build Now

# Tear down
docker compose -f honeypots/docker-compose.yml down
```

## Project Structure

```
HoneyMesh/
├── honeypots/
│   ├── cowrie/Dockerfile        # SSH honeypot image
│   ├── dionaea/Dockerfile       # Multi-protocol honeypot image
│   └── docker-compose.yml       # Full stack composition
├── k8s/
│   ├── cowrie-deployment.yml    # K8s Deployment + Service
│   ├── dionaea-deployment.yml   # K8s Deployment + Service
│   └── hpa.yml                  # Horizontal Pod Autoscaler
├── jenkins/
│   └── Jenkinsfile              # 6-stage CI/CD pipeline
├── ansible/
│   ├── inventory.ini            # Target hosts
│   └── playbook.yml             # Deploy HoneyMesh tasks
├── terraform/
│   └── main.tf                  # IaC: dirs, inventory, compose
├── monitoring/
│   ├── prometheus.yml           # Scrape configs
│   └── grafana-dashboard.json  # 4-panel attacker intel dashboard
├── dashboard/
│   ├── app.py                   # Flask + Prometheus metrics
│   ├── templates/index.html     # Dark cybersecurity UI
│   └── requirements.txt
├── sonarqube/
│   └── sonar-project.properties
└── README.md
```
