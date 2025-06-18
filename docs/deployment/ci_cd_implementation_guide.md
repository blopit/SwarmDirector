# CI/CD Implementation Guide

<!-- Version: 1.0 • Last updated: 2025-06-18 • Author: SwarmDirector Team -->

This guide provides comprehensive instructions for implementing and managing CI/CD pipelines for SwarmDirector, including automated testing, security scanning, deployment automation, and monitoring.

## 📋 Table of Contents

1. [Pipeline Overview](#pipeline-overview)
2. [GitHub Actions Implementation](#github-actions-implementation)
3. [Security Scanning Integration](#security-scanning-integration)
4. [Environment-Specific Deployments](#environment-specific-deployments)
5. [Monitoring and Notifications](#monitoring-and-notifications)
6. [Rollback Strategies](#rollback-strategies)
7. [Best Practices](#best-practices)

## 🔄 Pipeline Overview

### Pipeline Architecture

```
Code Push → Lint & Format → Security Scan → Unit Tests → Integration Tests → Build Docker Image
    ↓
Branch Check:
├── develop → Deploy to Staging → Staging Tests → Notify Team
└── main → Deploy to Production → Production Health Check → Notify Team
```

### Pipeline Stages

1. **Code Quality**: Linting, formatting, and static analysis
2. **Security Scanning**: Vulnerability assessment and dependency checks
3. **Testing**: Unit tests, integration tests, and coverage reporting
4. **Build**: Docker image creation and artifact generation
5. **Deployment**: Environment-specific deployment automation
6. **Verification**: Post-deployment health checks and smoke tests
7. **Notification**: Team alerts and status updates

## 🚀 GitHub Actions Implementation

### Enhanced CI/CD Workflow

```yaml
# .github/workflows/ci_cd_pipeline.yml
name: SwarmDirector CI/CD Pipeline

on:
  push:
    branches: [main, develop, feature/*]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:
    inputs:
      task_id:
        description: 'Task ID to associate with deployment'
        required: false
        type: string
      environment:
        description: 'Target environment'
        required: false
        default: 'staging'
        type: choice
        options:
        - staging
        - production

env:
  PYTHON_VERSION: '3.11'
  DOCKER_REGISTRY: ghcr.io
  IMAGE_NAME: swarmdirector

jobs:
  quality_check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install black isort flake8 pylint bandit safety

      - name: Code formatting check
        run: |
          black --check --diff src/
          isort --check-only --diff src/

      - name: Linting
        run: |
          flake8 src/
          pylint src/swarm_director/

      - name: Security scanning with Bandit
        run: |
          bandit -r src/ -f json -o security-report.json || true

      - name: Dependency vulnerability check
        run: |
          safety check --json --output safety-report.json || true

      - name: Upload security artifacts
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            security-report.json
            safety-report.json
```

## 🔒 Security Scanning Integration

### Comprehensive Security Pipeline

```yaml
# .github/workflows/security_scan.yml
name: Security Scanning Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * 0'  # Weekly scan on Sundays

jobs:
  security_scan:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Static Application Security Testing (SAST)
        run: |
          pip install bandit safety
          bandit -r src/ -f json -o bandit-report.json
          safety check --json --output safety-report.json

      - name: Secret scanning
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: main
          head: HEAD
          extra_args: --debug --only-verified

      - name: Container image scanning
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'python:3.11-slim'
          format: 'sarif'
          output: 'trivy-results.sarif'
```

## 🌐 Environment-Specific Deployments

### Staging Environment Configuration

```yaml
# deploy/staging/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: swarmdirector-staging
  namespace: swarmdirector-staging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: swarmdirector
      environment: staging
  template:
    spec:
      containers:
      - name: swarmdirector
        image: ${DOCKER_REGISTRY}/${GITHUB_REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}
        env:
        - name: FLASK_ENV
          value: "staging"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: swarmdirector-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Production Environment Configuration

```yaml
# deploy/production/deployment-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: swarmdirector-green
  namespace: swarmdirector-production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: swarmdirector
      environment: production
      version: green
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: swarmdirector
        image: ${DOCKER_REGISTRY}/${GITHUB_REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}
        env:
        - name: FLASK_ENV
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## 📊 Monitoring and Notifications

### Health Check Script

```bash
#!/bin/bash
# scripts/health_check.sh

ENVIRONMENT=${1:-staging}
HEALTH_ENDPOINT="https://${ENVIRONMENT}.swarmdirector.com/health"

echo "Checking health of ${ENVIRONMENT} environment..."

for i in {1..10}; do
    if curl -f -s "${HEALTH_ENDPOINT}" > /dev/null; then
        echo "✅ Health check passed for ${ENVIRONMENT}"
        exit 0
    else
        echo "❌ Health check failed, attempt $i/10"
        sleep 10
    fi
done

echo "❌ Health check failed after 10 attempts"
exit 1
```

## 🔄 Rollback Strategies

### Automated Rollback Script

```bash
#!/bin/bash
# scripts/rollback.sh

ENVIRONMENT=${1:-staging}
NAMESPACE="swarmdirector-${ENVIRONMENT}"

echo "Initiating rollback for ${ENVIRONMENT} environment..."

case "$ENVIRONMENT" in
    "staging")
        kubectl rollout undo deployment/swarmdirector-staging -n "$NAMESPACE"
        kubectl rollout status deployment/swarmdirector-staging -n "$NAMESPACE"
        ;;
    "production")
        echo "Switching traffic back to blue environment..."
        kubectl patch service swarmdirector-service -n "$NAMESPACE" \
            -p '{"spec":{"selector":{"version":"blue"}}}'
        
        kubectl scale deployment swarmdirector-blue -n "$NAMESPACE" --replicas=5
        kubectl rollout status deployment swarmdirector-blue -n "$NAMESPACE"
        ;;
esac

echo "Rollback completed for ${ENVIRONMENT}"
```

## 📋 Best Practices

### 1. Pipeline Security
- **Secret Management**: Use GitHub Secrets for sensitive data
- **Least Privilege**: Grant minimal permissions to workflow tokens
- **Container Scanning**: Scan all images for vulnerabilities
- **Dependency Checking**: Regular security updates for dependencies

### 2. Testing Strategy
- **Unit Tests**: Comprehensive test coverage (>80%)
- **Integration Tests**: Database and external service testing
- **End-to-End Tests**: Critical user journey validation
- **Performance Tests**: Load and stress testing

### 3. Deployment Patterns
- **Blue-Green Deployments**: Zero-downtime production deployments
- **Canary Releases**: Gradual rollout for risk mitigation
- **Feature Flags**: Safe feature deployment and rollback
- **Health Checks**: Comprehensive application monitoring

### 4. Monitoring and Observability
- **Application Metrics**: Performance and business metrics
- **Infrastructure Monitoring**: Resource utilization tracking
- **Log Aggregation**: Centralized logging with structured logs
- **Alerting**: Proactive issue detection and notification

---

*This guide provides comprehensive CI/CD implementation patterns for SwarmDirector.*
