---
title: Deployment Documentation Directory
description: Deployment guides and infrastructure documentation for SwarmDirector
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [deployment, infrastructure, devops, docker, kubernetes]
---

# Deployment Documentation Directory

## Purpose

The docs/deployment directory contains comprehensive deployment guides, infrastructure documentation, and DevOps procedures for SwarmDirector. This directory provides step-by-step instructions for deploying the application across different environments, from local development to production infrastructure.

## Structure

```
docs/deployment/
├── local_development.md        # Local development environment setup
├── docker_deployment.md        # Docker containerization and deployment
├── kubernetes_deployment.md    # Kubernetes deployment guide
├── cloud_deployment.md         # Cloud platform deployment guides
├── production_deployment.md    # Production deployment procedures
├── monitoring_setup.md         # Monitoring and observability setup
├── backup_recovery.md          # Backup and disaster recovery procedures
├── security_hardening.md       # Security hardening guidelines
├── performance_tuning.md       # Performance optimization guide
├── troubleshooting.md          # Deployment troubleshooting guide
├── environments/               # Environment-specific configurations
│   ├── development.md          # Development environment configuration
│   ├── staging.md              # Staging environment configuration
│   ├── production.md           # Production environment configuration
│   └── testing.md              # Testing environment configuration
├── infrastructure/             # Infrastructure as Code (IaC)
│   ├── terraform/              # Terraform configurations
│   │   ├── main.tf             # Main Terraform configuration
│   │   ├── variables.tf        # Variable definitions
│   │   ├── outputs.tf          # Output definitions
│   │   ├── modules/            # Terraform modules
│   │   │   ├── vpc/            # VPC module
│   │   │   ├── database/       # Database module
│   │   │   ├── compute/        # Compute resources module
│   │   │   └── monitoring/     # Monitoring module
│   │   └── environments/       # Environment-specific configs
│   │       ├── dev.tfvars      # Development variables
│   │       ├── staging.tfvars  # Staging variables
│   │       └── prod.tfvars     # Production variables
│   ├── ansible/                # Ansible playbooks
│   │   ├── site.yml            # Main playbook
│   │   ├── inventory/          # Inventory files
│   │   ├── roles/              # Ansible roles
│   │   │   ├── common/         # Common configuration role
│   │   │   ├── database/       # Database setup role
│   │   │   ├── application/    # Application deployment role
│   │   │   └── monitoring/     # Monitoring setup role
│   │   └── group_vars/         # Group variables
│   └── helm/                   # Helm charts for Kubernetes
│       ├── Chart.yaml          # Helm chart metadata
│       ├── values.yaml         # Default values
│       ├── templates/          # Kubernetes templates
│       │   ├── deployment.yaml # Application deployment
│       │   ├── service.yaml    # Service definition
│       │   ├── ingress.yaml    # Ingress configuration
│       │   ├── configmap.yaml  # Configuration map
│       │   └── secret.yaml     # Secret management
│       └── values/             # Environment-specific values
│           ├── dev-values.yaml # Development values
│           ├── staging-values.yaml # Staging values
│           └── prod-values.yaml # Production values
├── scripts/                    # Deployment automation scripts
│   ├── deploy.sh               # Main deployment script
│   ├── setup_environment.sh    # Environment setup script
│   ├── database_migration.sh   # Database migration script
│   ├── backup_database.sh      # Database backup script
│   ├── health_check.sh         # Health check script
│   ├── rollback.sh             # Rollback script
│   └── monitoring_setup.sh     # Monitoring setup script
├── ci_cd/                      # CI/CD pipeline configurations
│   ├── github_actions/         # GitHub Actions workflows
│   │   ├── ci.yml              # Continuous Integration
│   │   ├── cd.yml              # Continuous Deployment
│   │   ├── security_scan.yml   # Security scanning
│   │   └── performance_test.yml # Performance testing
│   ├── jenkins/                # Jenkins pipeline configurations
│   │   ├── Jenkinsfile         # Main pipeline
│   │   ├── deploy_pipeline.groovy # Deployment pipeline
│   │   └── test_pipeline.groovy # Testing pipeline
│   └── gitlab_ci/              # GitLab CI configurations
│       ├── .gitlab-ci.yml      # Main CI/CD configuration
│       ├── deploy.yml          # Deployment jobs
│       └── test.yml            # Testing jobs
└── configurations/             # Configuration templates and examples
    ├── nginx/                  # Nginx configurations
    │   ├── nginx.conf          # Main Nginx configuration
    │   ├── ssl.conf            # SSL configuration
    │   └── upstream.conf       # Upstream configuration
    ├── systemd/                # Systemd service files
    │   ├── swarmdirector.service # Main application service
    │   └── swarmdirector-worker.service # Worker service
    ├── docker/                 # Docker configurations
    │   ├── Dockerfile          # Application Dockerfile
    │   ├── docker-compose.yml  # Docker Compose configuration
    │   ├── docker-compose.prod.yml # Production Docker Compose
    │   └── .dockerignore       # Docker ignore file
    └── environment/            # Environment configuration templates
        ├── .env.template       # Environment variables template
        ├── config.yaml.template # YAML configuration template
        └── secrets.yaml.template # Secrets template
```

## Guidelines

### 1. Organization
- **Environment Separation**: Separate configurations by deployment environment
- **Infrastructure as Code**: Use IaC tools for reproducible infrastructure
- **Automation**: Automate deployment processes with scripts and CI/CD
- **Documentation**: Provide comprehensive deployment documentation

### 2. Naming
- **Descriptive Names**: Use clear, descriptive names for all deployment files
- **Environment Prefixes**: Use environment prefixes for environment-specific files
- **Version Indicators**: Include version information where relevant
- **Consistent Format**: Follow consistent naming conventions

### 3. Implementation
- **Containerization**: Use Docker for consistent deployment environments
- **Orchestration**: Use Kubernetes for container orchestration
- **Configuration Management**: Use configuration management tools
- **Monitoring**: Include monitoring and observability in deployments
- **Security**: Implement security best practices in all deployments

### 4. Documentation
- **Step-by-Step Guides**: Provide detailed deployment instructions
- **Prerequisites**: Document all prerequisites and dependencies
- **Configuration**: Document all configuration options and settings
- **Troubleshooting**: Include troubleshooting guides for common issues
- **Best Practices**: Document deployment best practices and recommendations

## Best Practices

### Docker Deployment
```dockerfile
# Dockerfile - Multi-stage build for production
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Create non-root user
RUN groupadd -r swarmdirector && useradd -r -g swarmdirector swarmdirector

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/swarmdirector/.local

# Copy application code
COPY --chown=swarmdirector:swarmdirector . .

# Set environment variables
ENV PATH=/home/swarmdirector/.local/bin:$PATH
ENV PYTHONPATH=/app/src
ENV FLASK_APP=src/swarm_director/app.py
ENV FLASK_ENV=production

# Switch to non-root user
USER swarmdirector

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "src.swarm_director.app:create_app()"]
```

### Security
- **Container Security**: Use minimal base images and non-root users
- **Secret Management**: Use proper secret management tools
- **Network Security**: Implement network segmentation and firewalls
- **Access Control**: Implement proper access controls and authentication
- **Encryption**: Use encryption for data in transit and at rest

### Performance
- **Resource Optimization**: Optimize resource allocation and usage
- **Caching**: Implement caching strategies for better performance
- **Load Balancing**: Use load balancing for high availability
- **Auto-scaling**: Implement auto-scaling based on demand
- **Monitoring**: Monitor performance metrics and optimize accordingly

### Testing
```yaml
# ci_cd/github_actions/ci.yml - CI pipeline with testing
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: swarmdirector_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        flake8 src tests
        black --check src tests
        isort --check-only src tests
    
    - name: Run type checking
      run: mypy src
    
    - name: Run security scan
      run: bandit -r src
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/swarmdirector_test
      run: |
        pytest tests/ --cov=src --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Build Docker image
      run: docker build -t swarmdirector:${{ github.sha }} .
    
    - name: Test Docker image
      run: |
        docker run --rm -d --name test-container -p 8000:8000 swarmdirector:${{ github.sha }}
        sleep 10
        curl -f http://localhost:8000/health || exit 1
        docker stop test-container
```

### Monitoring and Observability
- **Application Monitoring**: Monitor application performance and health
- **Infrastructure Monitoring**: Monitor infrastructure resources and health
- **Log Aggregation**: Centralize log collection and analysis
- **Alerting**: Implement alerting for critical issues
- **Dashboards**: Create monitoring dashboards for visibility

## Examples

### Kubernetes Deployment
```yaml
# infrastructure/helm/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "swarmdirector.fullname" . }}
  labels:
    {{- include "swarmdirector.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "swarmdirector.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}
      labels:
        {{- include "swarmdirector.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "swarmdirector.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: {{ include "swarmdirector.fullname" . }}-secret
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: {{ include "swarmdirector.fullname" . }}-secret
                  key: redis-url
          envFrom:
            - configMapRef:
                name: {{ include "swarmdirector.fullname" . }}-config
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          volumeMounts:
            - name: config-volume
              mountPath: /app/config
              readOnly: true
            - name: logs-volume
              mountPath: /app/logs
      volumes:
        - name: config-volume
          configMap:
            name: {{ include "swarmdirector.fullname" . }}-config
        - name: logs-volume
          emptyDir: {}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

### Terraform Infrastructure
```hcl
# infrastructure/terraform/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "swarmdirector-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-west-2"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "SwarmDirector"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
  
  availability_zones = var.availability_zones
  public_subnets     = var.public_subnets
  private_subnets    = var.private_subnets
  database_subnets   = var.database_subnets
  
  enable_nat_gateway = var.enable_nat_gateway
  enable_vpn_gateway = var.enable_vpn_gateway
}

# Database Module
module "database" {
  source = "./modules/database"
  
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.database_subnets
  
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  engine_version    = var.db_engine_version
  
  backup_retention_period = var.db_backup_retention_period
  backup_window          = var.db_backup_window
  maintenance_window     = var.db_maintenance_window
  
  monitoring_interval = var.db_monitoring_interval
  performance_insights_enabled = var.db_performance_insights_enabled
}

# Compute Module
module "compute" {
  source = "./modules/compute"
  
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
  
  instance_type = var.instance_type
  min_size      = var.asg_min_size
  max_size      = var.asg_max_size
  desired_size  = var.asg_desired_size
  
  key_name = var.key_name
  
  database_endpoint = module.database.endpoint
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"
  
  environment = var.environment
  
  enable_cloudwatch = var.enable_cloudwatch
  enable_xray       = var.enable_xray
  
  log_retention_days = var.log_retention_days
  
  notification_email = var.notification_email
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "database_endpoint" {
  description = "Database endpoint"
  value       = module.database.endpoint
  sensitive   = true
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = module.compute.load_balancer_dns
}
```

### Deployment Script
```bash
#!/bin/bash
# scripts/deploy.sh - Main deployment script

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-development}"
VERSION="${2:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validation functions
validate_environment() {
    case "$ENVIRONMENT" in
        development|staging|production)
            log_info "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("docker" "kubectl" "helm")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

build_application() {
    log_info "Building application..."
    
    cd "$PROJECT_ROOT"
    
    # Build Docker image
    docker build -t "swarmdirector:$VERSION" .
    
    # Tag for registry
    docker tag "swarmdirector:$VERSION" "registry.example.com/swarmdirector:$VERSION"
    
    log_info "Application built successfully"
}

run_tests() {
    log_info "Running tests..."
    
    cd "$PROJECT_ROOT"
    
    # Run unit tests
    python -m pytest tests/unit/ -v
    
    # Run integration tests
    python -m pytest tests/integration/ -v
    
    # Run security tests
    bandit -r src/
    
    log_info "All tests passed"
}

deploy_database_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Run Alembic migrations
    alembic upgrade head
    
    log_info "Database migrations completed"
}

deploy_application() {
    log_info "Deploying application to $ENVIRONMENT..."
    
    cd "$PROJECT_ROOT/docs/deployment/infrastructure/helm"
    
    # Update Helm dependencies
    helm dependency update
    
    # Deploy with Helm
    helm upgrade --install swarmdirector . \
        --namespace "swarmdirector-$ENVIRONMENT" \
        --create-namespace \
        --values "values/$ENVIRONMENT-values.yaml" \
        --set image.tag="$VERSION" \
        --wait \
        --timeout=10m
    
    log_info "Application deployed successfully"
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Wait for deployment to be ready
    kubectl wait --for=condition=available deployment/swarmdirector \
        --namespace="swarmdirector-$ENVIRONMENT" \
        --timeout=300s
    
    # Get service URL
    local service_url
    service_url=$(kubectl get service swarmdirector \
        --namespace="swarmdirector-$ENVIRONMENT" \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    # Health check
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f "http://$service_url/health" &> /dev/null; then
            log_info "Health check passed"
            return 0
        fi
        
        log_warn "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Health checks failed after $max_attempts attempts"
    return 1
}

cleanup() {
    log_info "Cleaning up..."
    
    # Remove old Docker images
    docker image prune -f
    
    log_info "Cleanup completed"
}

main() {
    log_info "Starting deployment process..."
    
    validate_environment
    check_prerequisites
    build_application
    run_tests
    deploy_database_migrations
    deploy_application
    run_health_checks
    cleanup
    
    log_info "Deployment completed successfully!"
}

# Error handling
trap 'log_error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"
```

## Related Documentation

- [Local Development](local_development.md) - Local development environment setup
- [Docker Deployment](docker_deployment.md) - Docker containerization guide
- [Kubernetes Deployment](kubernetes_deployment.md) - Kubernetes deployment guide
- [Production Deployment](production_deployment.md) - Production deployment procedures
- [Monitoring Setup](monitoring_setup.md) - Monitoring and observability setup
- [Security Hardening](security_hardening.md) - Security hardening guidelines
- [Architecture Documentation](../architecture/README.md) - System architecture overview
