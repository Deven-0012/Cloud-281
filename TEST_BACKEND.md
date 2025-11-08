# Testing Backend Services

## Prerequisites

1. **Start Docker Desktop** - Make sure Docker Desktop is running on your Mac
2. **Check Docker is running**:
   ```bash
   docker ps
   ```
   Should not give an error

## Option 1: Quick Test (Recommended)

Run the test script:
```bash
./test_backend.sh
```

This will:
- Check Docker is running
- Start database services
- Start ingestion service
- Test the health endpoint

## Option 2: Manual Test

### Step 1: Start Docker Desktop
Open Docker Desktop application on your Mac and wait for it to start.

### Step 2: Start Services

```bash
# Start all services
docker compose up -d

# OR start just backend services
docker compose up -d postgres mongodb redis ingestion-service
```

### Step 3: Wait for Services to Start
```bash
# Watch logs
docker compose logs -f ingestion-service

# Wait until you see: "Running on http://0.0.0.0:5001"
```

### Step 4: Test Health Endpoint
```bash
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-06T...",
  "service": "audio-ingestion-service"
}
```

### Step 5: Test Other Endpoints

```bash
# Get dashboard stats
curl http://localhost:5001/v1/dashboard/stats

# Get alerts
curl http://localhost:5001/v1/alerts

# Get vehicles
curl http://localhost:5001/v1/vehicles
```

## Troubleshooting

### Docker not running
```bash
# Error: "Cannot connect to Docker daemon"
# Solution: Start Docker Desktop application
```

### Port already in use
```bash
# Error: "port is already allocated"
# Solution: Stop existing containers
docker compose down
```

### Service not starting
```bash
# Check logs
docker compose logs ingestion-service

# Check service status
docker compose ps
```

### Database connection errors
```bash
# Wait for database to be ready
docker compose exec postgres pg_isready

# Check database logs
docker compose logs postgres
```

## View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ingestion-service
docker compose logs -f ml-worker
docker compose logs -f alert-engine
```

## Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v
```

