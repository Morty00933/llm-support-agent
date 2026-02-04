# Infrastructure Documentation

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Docker Configuration](#docker-configuration)
- [Makefile Commands](#makefile-commands)
- [Environment Variables](#environment-variables)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Development

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start all services
make dev

# 3. Download AI models (first time only)
make ollama-pull

# 4. Access the application
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Production

```bash
# 1. Set production environment variables
cp .env.example .env.prod
# Edit .env.prod with production values

# 2. Generate strong JWT secret
openssl rand -hex 32  # Copy output to JWT_SECRET in .env.prod

# 3. Start production stack
make prod

# 4. Optional: Start monitoring
make monitoring
```

---

## 🏗️ Architecture

### Service Overview

```
┌─────────────────────────────────────────────────────────┐
│                      FRONTEND                            │
│        (React + Vite + Nginx) :3000                     │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────┐
│                     BACKEND API                          │
│           (FastAPI + Python 3.11) :8000                 │
└───────┬──────────┬──────────┬──────────┬───────────────┘
        │          │          │          │
        ↓          ↓          ↓          ↓
    ┌───────┐  ┌──────┐  ┌───────┐  ┌────────┐
    │Postgres│  │Redis │  │Ollama │  │Celery  │
    │:5432   │  │:6379 │  │:11434 │  │Worker  │
    └────────┘  └──────┘  └───────┘  └────────┘
```

### Service Responsibilities

| Service    | Purpose                          | Port  | Data Volume |
|------------|----------------------------------|-------|-------------|
| Frontend   | React SPA, static assets         | 3000  | None        |
| Backend    | REST API, WebSocket, business logic | 8000 | None   |
| PostgreSQL | Primary database with pgvector   | 5432  | postgres_data |
| Redis      | Cache, rate limiting, Celery broker | 6379 | redis_data |
| Ollama     | LLM inference (chat & embeddings) | 11434 | ollama_data |
| Celery     | Background tasks (embeddings, etc) | -   | None       |

---

## 🐳 Docker Configuration

### Multi-Stage Dockerfiles

#### Backend (Dockerfile.backend)

```
Stage 1: base        → System dependencies
Stage 2: builder     → Compile Python packages
Stage 3: development → Dev tools + hot-reload
Stage 4: production  → Minimal, optimized image
```

**Development Features:**
- Code mounted as volume (hot-reload)
- Development tools (pytest-watch, ipython, debugpy)
- Less strict healthchecks

**Production Features:**
- Code baked into image (immutable)
- ~40% smaller image size
- Non-root user
- Strict healthchecks
- No dev dependencies

#### Frontend (frontend/Dockerfile)

```
Stage 1: development → Vite dev server
Stage 2: builder     → npm build
Stage 3: production  → Nginx + static files
```

**Development:**
- Vite dev server with HMR
- Port 3000

**Production:**
- Nginx serving static files
- Gzip compression
- Security headers
- Port 3000 (can map to 80/443)

### Docker Compose Files

| File                          | Purpose                          | Usage                |
|-------------------------------|----------------------------------|----------------------|
| docker-compose.yml            | Development environment          | `make dev`           |
| docker-compose.prod.yml       | Production environment           | `make prod`          |
| docker-compose.gpu.yml        | GPU support (overlay)            | `make dev-gpu`       |
| docker-compose.monitoring.yml | Prometheus + Grafana             | `make monitoring`    |

### Environment-Specific Differences

| Feature               | Development                  | Production                  |
|-----------------------|------------------------------|-----------------------------|
| **Code Mounting**     | ✅ Volume mount (hot-reload) | ❌ Baked into image         |
| **Debug Mode**        | ✅ Enabled                   | ❌ Disabled                 |
| **Image Size**        | Larger (dev tools)           | 40% smaller                 |
| **Restart Policy**    | unless-stopped               | always                      |
| **Resource Limits**   | None                         | CPU/Memory limits           |
| **Port Binding**      | 0.0.0.0:port                 | 127.0.0.1:port (localhost)  |
| **Replicas**          | 1                            | 2+ (with load balancer)     |
| **Healthchecks**      | Relaxed timings              | Strict timings              |

---

## 🛠️ Makefile Commands

### Development

```bash
make dev                # Start development environment
make dev-full           # Start with Celery worker
make dev-gpu            # Start with GPU support
make monitoring         # Start Prometheus + Grafana
```

### Control

```bash
make stop               # Stop all services
make restart            # Restart all services
make restart-backend    # Restart backend only
make restart-frontend   # Restart frontend only
```

### Logs

```bash
make logs               # View all logs (follow)
make logs-backend       # View backend logs only
make logs-frontend      # View frontend logs only
make logs-ollama        # View Ollama logs only
make logs-celery        # View Celery worker logs
```

### Build

```bash
make build              # Build all containers
make build-backend      # Build backend only
make build-frontend     # Build frontend only
make build-no-cache     # Rebuild without cache
```

### Database

```bash
make migrate            # Run database migrations
make migrate-down       # Rollback last migration
make migrate-create NAME=description  # Create new migration
make db-shell           # Open PostgreSQL shell
make db-reset           # Reset database (WARNING: destroys data)
```

### Ollama

```bash
make ollama-pull        # Download AI models
make ollama-list        # List available models
make ollama-rm MODEL=name  # Remove a model
```

### Testing

```bash
make test               # Run all tests
make test-cov           # Run tests with coverage
make test-unit          # Run unit tests only
make test-e2e           # Run E2E tests only
make test-watch         # Run tests in watch mode
make lint               # Run linter (ruff)
make lint-fix           # Auto-fix linting issues
make typecheck          # Run type checking (mypy)
make format             # Format code with ruff
```

### Shell Access

```bash
make shell              # Open backend container shell
make shell-backend      # Open backend container shell
make shell-frontend     # Open frontend container shell
make redis-cli          # Open Redis CLI
```

### Cleanup

```bash
make clean              # Stop and remove containers/networks
make clean-volumes      # Remove all volumes (WARNING: deletes data)
make clean-all          # Remove everything including images
```

### Monitoring

```bash
make status             # Show service status
make health             # Check service health
make stats              # Show container resource usage
```

### Utilities

```bash
make seed-demo          # Seed demo data
make backup-db          # Backup database to ./backups/
make restore-db FILE=path/to/backup.sql  # Restore database
```

---

## 🔧 Environment Variables

### Critical Variables (MUST configure for production)

```bash
# Security
JWT_SECRET=<openssl rand -hex 32>          # CRITICAL: Generate strong secret
DB_PASSWORD=<strong-password>               # Database password
REDIS_PASSWORD=<strong-password>            # Redis password (if exposed)

# Application
ENV=prod                                    # Environment: dev, test, prod
DEBUG=false                                 # MUST be false in production
CORS_ORIGINS=https://yourdomain.com         # Production domain(s) only

# Monitoring
SENTRY_DSN=https://your-sentry-dsn          # Error tracking
```

### Database Configuration

```bash
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres                        # CHANGE IN PRODUCTION
DB_NAME=llm_agent
DB_POOL_SIZE=10                            # Connection pool size
DB_MAX_OVERFLOW=20                         # Max extra connections
```

### Redis Configuration

```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=                            # Set in production
REDIS_DB=0                                 # Database number (0-15)
```

### Ollama Configuration

```bash
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL_CHAT=qwen2.5:3b              # Chat model
OLLAMA_MODEL_EMBED=nomic-embed-text        # Embedding model
OLLAMA_TIMEOUT=120                         # Request timeout (seconds)
OLLAMA_TEMPERATURE=0.2                     # Response creativity (0.0-1.0)
```

### Feature Flags

```bash
PROMETHEUS_ENABLED=true                    # Enable metrics endpoint
DEMO_MODE_ENABLED=false                    # Enable demo endpoints
DEMO_SEED_ON_STARTUP=false                 # Auto-seed demo data
FEATURE_DARK_MODE=true                     # Enable dark mode UI
```

---

## 🚀 Production Deployment

### Prerequisites

1. **Server Requirements:**
   - Linux server (Ubuntu 22.04 LTS recommended)
   - Docker 24.0+ and Docker Compose V2
   - Minimum 4GB RAM, 2 CPU cores
   - Recommended 8GB RAM, 4 CPU cores

2. **Security:**
   - Firewall configured (ports 80, 443, 22)
   - SSL/TLS certificates (Let's Encrypt recommended)
   - Strong passwords for all services

### Deployment Steps

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin
```

#### 2. Application Setup

```bash
# Clone repository
git clone <your-repo-url>
cd llm-support-agent

# Create production environment file
cp .env.example .env.prod

# Generate JWT secret
openssl rand -hex 32

# Edit .env.prod with production values
nano .env.prod
```

#### 3. Configure Production Environment

```bash
# .env.prod essential settings
ENV=prod
DEBUG=false
JWT_SECRET=<generated-secret>
DB_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
CORS_ORIGINS=https://yourdomain.com
SENTRY_DSN=<your-sentry-dsn>
LOG_LEVEL=WARNING
```

#### 4. Deploy

```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Download Ollama models
docker-compose exec ollama ollama pull qwen2.5:3b
docker-compose exec ollama ollama pull nomic-embed-text

# Run migrations
docker-compose exec backend alembic upgrade head

# Check health
make health
```

#### 5. Setup Monitoring (Optional)

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana at http://your-server:3001
# Default credentials: admin/admin (change immediately)
```

### SSL/TLS Setup with Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/llm-support-agent
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /v1/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Backups

```bash
# Automated backup script
#!/bin/bash
# /opt/scripts/backup-llm-agent.sh

BACKUP_DIR="/backups/llm-agent"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker exec llm-support-db-prod pg_dump -U postgres llm_agent > \
    $BACKUP_DIR/db_$DATE.sql

# Backup volumes
docker run --rm -v postgres_data:/data -v $BACKUP_DIR:/backup \
    ubuntu tar czf /backup/postgres_data_$DATE.tar.gz /data

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```cron
# Add to crontab: crontab -e
0 2 * * * /opt/scripts/backup-llm-agent.sh
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Services Won't Start

```bash
# Check logs
make logs

# Check service status
make status

# Check health
make health

# Restart services
make restart
```

#### 2. Database Connection Errors

```bash
# Check if PostgreSQL is ready
docker-compose exec postgres pg_isready -U postgres

# Check database connectivity
make db-shell
```

#### 3. Ollama Models Not Found

```bash
# Download models
make ollama-pull

# Verify models
make ollama-list

# Check Ollama logs
make logs-ollama
```

#### 4. Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Change port in .env
PORT=8001

# Restart
make restart-backend
```

#### 5. Out of Memory

```bash
# Check container resource usage
make stats

# Increase Docker memory limit in Docker Desktop settings
# Or add memory limits to docker-compose.yml
```

#### 6. Hot-Reload Not Working

```bash
# Ensure volume mounts are correct
docker-compose config

# Restart with rebuild
make stop
make dev
```

### Debug Mode

```bash
# Enable debug logging
echo "LOG_LEVEL=DEBUG" >> .env
make restart-backend

# View detailed logs
make logs-backend
```

### Performance Tuning

#### PostgreSQL

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

#### Redis

```bash
# Monitor Redis in real-time
make redis-cli
> MONITOR

# Check memory usage
> INFO memory

# Check hit/miss ratio
> INFO stats
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Ollama Documentation](https://ollama.ai/docs)

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `make logs`
2. Check health: `make health`
3. Check GitHub Issues
4. Contact support
