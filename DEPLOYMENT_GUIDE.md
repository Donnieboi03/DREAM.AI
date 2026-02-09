# DREAM.AI Production Docker Deployment Guide

## ✅ Files Created

All production files have been set up:

- ✅ `Dockerfile.prod` - Optimized production backend image
- ✅ `dreamai/frontend/Dockerfile` - Production frontend image
- ✅ `docker-compose.yml` - Full stack orchestration (backend, frontend, nginx)
- ✅ `nginx.conf` - Reverse proxy with SSL support
- ✅ `.env.prod` - Production environment configuration
- ✅ `k8s-deployment.yaml` - Kubernetes deployment manifests
- ✅ `.dockerignore` - Optimized build context

## 🚀 Quick Start - Local Docker Testing

### Step 1: Build Docker Images

```bash
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI
docker-compose build
```

Expected output:
```
[+] Building 45.3s
 => [backend builder base] ...
 => [frontend builder base] ...
 => [nginx] docker.io/library/nginx:alpine
Successfully tagged dreamai-backend:latest
Successfully tagged dreamai-frontend:latest
```

### Step 2: Start the Stack

```bash
docker-compose up -d
```

Expected output:
```
[+] Running 4/4
 ✔ Container dreamai-backend   Started   2.1s
 ✔ Container dreamai-frontend  Started   1.8s
 ✔ Container dreamai-nginx     Started   0.9s
```

### Step 3: Verify Services

Check all containers are healthy:
```bash
docker-compose ps
```

Expected output:
```
NAME                  STATUS
dreamai-backend       running (healthy)
dreamai-frontend      running (healthy)
dreamai-nginx         running
```

Check logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

### Step 4: Test Access

- **Frontend**: http://localhost
- **API Health**: http://localhost/health
- **WebSocket**: ws://localhost/ws/game

## 🧪 Testing Checklist

```bash
# 1. Check health endpoint
curl http://localhost/health

# Expected response:
# {"status":"ok","environment_initialized":true,"connected_clients":0}

# 2. Check frontend loads
curl http://localhost

# Expected: HTML page (React app)

# 3. Check WebSocket works
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost/ws/game

# Expected: 101 Switching Protocols

# 4. View in browser
# Open http://localhost in your web browser
```

## 🛑 Stop the Stack

```bash
docker-compose down
```

To remove volumes as well:
```bash
docker-compose down -v
```

## ☁️ Production Deployment

### Option A: Push to Docker Registry (AWS, Azure, GCP, DockerHub)

#### Example: Azure Container Registry

```bash
# Login to ACR
az acr login --name yourregistry

# Tag images
docker tag dreamai-backend:latest yourregistry.azurecr.io/dreamai-backend:latest
docker tag dreamai-frontend:latest yourregistry.azurecr.io/dreamai-frontend:latest

# Push images
docker push yourregistry.azurecr.io/dreamai-backend:latest
docker push yourregistry.azurecr.io/dreamai-frontend:latest

# Update docker-compose.yml image references:
# image: yourregistry.azurecr.io/dreamai-backend:latest
# image: yourregistry.azurecr.io/dreamai-frontend:latest

# Deploy
docker-compose -f docker-compose.yml up -d
```

#### Example: AWS ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag dreamai-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/dreamai-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/dreamai-backend:latest
```

### Option B: Kubernetes Deployment (GKE, AKS, EKS)

#### Prerequisites
- kubectl installed
- Kubernetes cluster running
- Container images pushed to registry

#### Deploy

```bash
# Update k8s-deployment.yaml:
# 1. Change 'your-registry' to your actual registry URL
# 2. Update 'yourdomain.com' to your domain

# Create namespace and deploy
kubectl apply -f k8s-deployment.yaml

# Check deployment status
kubectl -n dreamai get deployments
kubectl -n dreamai get pods
kubectl -n dreamai get svc

# View logs
kubectl -n dreamai logs -f deployment/dreamai-backend

# Scale deployments
kubectl -n dreamai scale deployment dreamai-backend --replicas=5

# Enable auto-scaling
kubectl -n dreamai get hpa
```

### Option C: Single Server (VPS/EC2/Droplet)

#### Prerequisites
- Ubuntu 20.04+ or similar
- Docker & Docker Compose installed
- Domain name (optional but recommended)
- SSL certificates (from Let's Encrypt)

#### Setup

```bash
# SSH into server
ssh user@your-server.com

# Clone repository
git clone <your-repo> dreamai
cd dreamai

# Copy production files
cp .env.prod .env

# Edit .env with production values
nano .env
# Set: SECRET_KEY, ALLOWED_HOSTS, CORS_ORIGINS, etc.

# (Optional) Setup SSL certificates
# Using certbot with Let's Encrypt
sudo apt-get install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates to ssl/ directory
mkdir ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*

# Build and run
docker-compose build
docker-compose up -d

# Enable auto-restart
# Add to crontab: @reboot cd ~/dreamai && docker-compose up -d
```

#### Monitor

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Check resource usage
docker stats

# Restart service
docker-compose restart backend
```

## 🔐 Security Checklist

Before going to production:

- [ ] Change `SECRET_KEY` in `.env.prod`
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Enable SSL/HTTPS (uncomment nginx HTTPS section)
- [ ] Setup rate limiting (already in nginx.conf)
- [ ] Enable authentication if needed
- [ ] Use secrets management (AWS Secrets Manager, Azure Key Vault, etc.)
- [ ] Setup monitoring and logging
- [ ] Configure auto-backups
- [ ] Setup uptime monitoring
- [ ] Test disaster recovery

## 📊 Monitoring & Logging

### Docker Compose

```bash
# Real-time logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Kubernetes

```bash
# Pod logs
kubectl -n dreamai logs -f pod/<pod-name>

# All backend logs
kubectl -n dreamai logs -f deployment/dreamai-backend

# Events
kubectl -n dreamai get events
```

## 🆘 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs backend

# Rebuild without cache
docker-compose build --no-cache backend

# Run with interactive shell for debugging
docker run -it dreamai-backend:latest /bin/bash
```

### Out of memory

```bash
# Check memory usage
docker stats

# Increase limits in docker-compose.yml:
# memory: 2Gi
# or in k8s-deployment.yaml:
# limits:
#   memory: 2Gi
```

### WebSocket connection fails

```bash
# Check nginx logs
docker-compose logs nginx

# Verify WebSocket path in nginx.conf
# Should be: location /ws/

# Check backend is receiving messages
docker-compose logs backend | grep WebSocket
```

### DNS resolution issues

```bash
# Test DNS
nslookup yourdomain.com

# Clear DNS cache (on Mac):
sudo dscacheutil -flushcache

# On Linux:
sudo systemctl restart systemd-resolved
```

## 📈 Performance Optimization

### Backend

```yaml
# In docker-compose.yml:
environment:
  - FASTAPI_WORKERS=4  # Increase for CPU-bound tasks
  - LOG_LEVEL=warning  # Reduce logging overhead
resources:
  limits:
    memory: 4Gi
    cpus: 2
```

### Frontend

- Enable gzip compression (already in nginx.conf)
- Use CDN for static assets
- Enable browser caching

### Database (when added)

- Use read replicas
- Setup connection pooling
- Enable query caching

## 🔄 Continuous Deployment (CI/CD)

### GitHub Actions Example

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build images
        run: docker-compose build
      
      - name: Push to registry
        run: |
          docker login -u ${{ secrets.REGISTRY_USER }} -p ${{ secrets.REGISTRY_PASS }}
          docker push dreamai-backend:latest
      
      - name: Deploy to server
        run: |
          ssh ${{ secrets.SERVER }} 'cd dreamai && docker-compose pull && docker-compose up -d'
```

## 📝 Environment Variables Reference

```bash
# .env.prod - All available settings

ENVIRONMENT=production              # production / staging / development
DEBUG=false                          # Never true in production
PYTHONUNBUFFERED=1                 # Show logs immediately

AI2THOR_HEADLESS=1                 # Run without display
AI2THOR_TIMEOUT=30                 # Timeout in seconds

FASTAPI_LOG_LEVEL=info             # debug / info / warning / error
FASTAPI_WORKERS=1                  # 1 per CPU core

SECRET_KEY=change-this             # Used for session/token signing
ALLOWED_HOSTS=yourdomain.com       # Comma-separated
CORS_ORIGINS=[...]                 # Allowed origins

GEMINI_API_KEY=...                 # For LLM features (optional)
AWS_ACCESS_KEY_ID=...              # For S3 storage (optional)
```

## ✅ Ready to Deploy!

Your production setup is complete. Choose one of:

1. **Local testing**: `docker-compose up -d` → http://localhost
2. **Cloud deployment**: Push to registry + deploy to Kubernetes
3. **Server deployment**: Copy files to VPS + `docker-compose up -d`

**Next steps:**
1. Build and test locally
2. Verify all tests pass
3. Choose deployment target
4. Configure SSL certificates
5. Deploy!

Need help? Check the logs with `docker-compose logs -f`
