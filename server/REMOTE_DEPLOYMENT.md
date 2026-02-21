# Remote Deployment Guide - Team/Enterprise Mode

This guide shows how to deploy AWX MCP Server as a remote service for teams and organizations.

---

## 🎯 Deployment Options

1. [Docker Compose](#docker-compose) - Quick start, development
2. [Kubernetes](#kubernetes) - Production, scalable
3. [OpenShift](#openshift) - Enterprise, Red Hat
4. [Cloud Platforms](#cloud-platforms) - Managed services

---

## 🐳 Docker Compose

### Quick Start

```bash
cd server
docker-compose up -d
```

### Configuration

The server accepts credentials from clients in two ways:

#### Option 1: Client-Provided Credentials (Recommended)

Clients send AWX credentials with each request. No credentials stored on server.

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  awx-mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      # Server configuration
      - LOG_LEVEL=info
      - CREDENTIAL_MODE=client_provided
      
      # Optional: Default AWX URL (can be overridden by client)
      - DEFAULT_AWX_URL=https://awx.example.com
      
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

**VS Code Client Configuration:**
```json
{
  "github.copilot.chat.mcpServers": {
    "awx-remote": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-sse", "http://localhost:8000"],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "${secret:awx-token}"
      }
    }
  }
}
```

#### Option 2: Server-Side Vault (Future - Placeholder)

Server retrieves credentials from vault based on user identity.

**See:** [VAULT_INTEGRATION.md](VAULT_INTEGRATION.md)

---

## ☸️ Kubernetes

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Ingress controller (nginx, traefik, etc.)
- TLS certificate

### Deploy

```bash
# Create namespace
kubectl create namespace awx-mcp

# Create secrets (if using server-side credentials)
kubectl create secret generic awx-credentials \
  --from-literal=awx-url=https://awx.example.com \
  --from-literal=awx-token=your-token \
  -n awx-mcp

# Deploy
kubectl apply -f deployment/kubernetes.yaml -n awx-mcp

# Verify
kubectl get pods -n awx-mcp
kubectl get svc -n awx-mcp
```

### Configuration

**deployment/kubernetes.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: awx-mcp-config
  namespace: awx-mcp
data:
  LOG_LEVEL: "info"
  CREDENTIAL_MODE: "client_provided"  # or "vault" (future)
  DEFAULT_AWX_URL: "https://awx.example.com"
  
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: awx-mcp-server
  namespace: awx-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: awx-mcp-server
  template:
    metadata:
      labels:
        app: awx-mcp-server
    spec:
      containers:
      - name: awx-mcp-server
        image: surgexlabs/awx-mcp-server:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: awx-mcp-config
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
          requests:
            cpu: "200m"
            memory: "256Mi"
            
---
apiVersion: v1
kind: Service
metadata:
  name: awx-mcp-server
  namespace: awx-mcp
spec:
  selector:
    app: awx-mcp-server
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: awx-mcp-server
  namespace: awx-mcp
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - awx-mcp.company.com
    secretName: awx-mcp-tls
  rules:
  - host: awx-mcp.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: awx-mcp-server
            port:
              number: 80
```

### Access

```bash
# Get external IP/URL
kubectl get ingress -n awx-mcp

# Test
curl https://awx-mcp.company.com/health
```

---

## 🔴 OpenShift

### Deploy

```bash
# Login
oc login

# Create project
oc new-project awx-mcp

# Deploy
oc apply -f deployment/kubernetes.yaml

# Create route
oc expose svc/awx-mcp-server --hostname=awx-mcp.apps.company.com

# Verify
oc get pods
oc get route
```

### OpenShift-Specific Configuration

```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: awx-mcp-server
  namespace: awx-mcp
spec:
  host: awx-mcp.apps.company.com
  to:
    kind: Service
    name: awx-mcp-server
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
```

---

## ☁️ Cloud Platforms

### AWS ECS

```bash
# Build and push to ECR
aws ecr create-repository --repository-name awx-mcp-server
docker build -t awx-mcp-server:latest .
docker tag awx-mcp-server:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/awx-mcp-server:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/awx-mcp-server:latest

# Create ECS task definition
aws ecs register-task-definition --cli-input-json file://deployment/aws-ecs-task.json

# Create service
aws ecs create-service \
  --cluster awx-cluster \
  --service-name awx-mcp-server \
  --task-definition awx-mcp-server \
  --desired-count 3 \
  --launch-type FARGATE \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=awx-mcp-server,containerPort=8000
```

### Azure Container Instances

```bash
az container create \
  --resource-group awx-mcp-rg \
  --name awx-mcp-server \
  --image surgexlabs/awx-mcp-server:latest \
  --dns-name-label awx-mcp \
  --ports 8000 \
  --environment-variables \
    LOG_LEVEL=info \
    CREDENTIAL_MODE=client_provided
```

### Google Cloud Run

```bash
gcloud run deploy awx-mcp-server \
  --image gcr.io/project-id/awx-mcp-server:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars LOG_LEVEL=info,CREDENTIAL_MODE=client_provided
```

---

## 🔐 Security Configuration

### TLS/SSL

**Required for production!** Credentials are transmitted from clients.

#### Let's Encrypt (Kubernetes)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@company.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Authentication (Future)

Placeholder for future authentication methods:
- OAuth2/OIDC
- API Keys
- mTLS
- LDAP/Active Directory

**See:** `server/src/awx_mcp_server/auth/` for placeholders

---

## 🔄 Client Configuration

### VS Code (Client-Provided Credentials)

```json
{
  "github.copilot.chat.mcpServers": {
    "awx-remote": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-sse",
        "https://awx-mcp.company.com"
      ],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "${secret:awx-token}",
        "AWX_ENVIRONMENT": "production"
      }
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "awx": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-sse",
        "https://awx-mcp.company.com"
      ],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "your-awx-token"
      }
    }
  }
}
```

### Switching Environments

Users can configure multiple remote servers for different environments:

```json
{
  "github.copilot.chat.mcpServers": {
    "awx-dev": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-sse", "https://awx-mcp.company.com"],
      "env": {
        "AWX_BASE_URL": "https://awx-dev.example.com",
        "AWX_TOKEN": "${secret:awx-dev-token}",
        "AWX_ENVIRONMENT": "development"
      }
    },
    "awx-prod": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-sse", "https://awx-mcp.company.com"],
      "env": {
        "AWX_BASE_URL": "https://awx-prod.example.com",
        "AWX_TOKEN": "${secret:awx-prod-token}",
        "AWX_ENVIRONMENT": "production"
      }
    }
  }
}
```

---

## 📊 Monitoring

### Health Check

```bash
curl https://awx-mcp.company.com/health
```

### Metrics (Prometheus)

```bash
curl https://awx-mcp.company.com/prometheus-metrics
```

### Logging

Configure centralized logging:

```yaml
# deployment/kubernetes.yaml
containers:
- name: awx-mcp-server
  env:
  - name: LOG_LEVEL
    value: "info"
  - name: LOG_FORMAT
    value: "json"  # For log aggregation
```

Integrate with:
- ELK Stack
- Splunk
- Datadog
- CloudWatch

---

## 🔧 Troubleshooting

### Connection Issues

```bash
# Check pods
kubectl get pods -n awx-mcp
kubectl logs -f <pod-name> -n awx-mcp

# Check ingress
kubectl describe ingress awx-mcp-server -n awx-mcp

# Test internally
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://awx-mcp-server.awx-mcp.svc.cluster.local/health
```

### Performance Issues

```bash
# Scale up replicas
kubectl scale deployment/awx-mcp-server --replicas=5 -n awx-mcp

# Check resource usage
kubectl top pods -n awx-mcp
```

---

## 📈 Scaling

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: awx-mcp-server
  namespace: awx-mcp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: awx-mcp-server
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 🔒 Vault Integration (Future)

For enterprise deployments with centralized credential management.

**See:** [VAULT_INTEGRATION.md](VAULT_INTEGRATION.md)

Placeholder files:
- `server/src/awx_mcp_server/storage/vault_integration.py`
- `config/vault-config.yaml`

---

## 📚 Additional Resources

- [Deployment Architecture](../DEPLOYMENT_ARCHITECTURE.md)
- [Quick Start Guide](QUICK_START.md)
- [Vault Integration](VAULT_INTEGRATION.md)
- [Security Best Practices](SECURITY.md)
