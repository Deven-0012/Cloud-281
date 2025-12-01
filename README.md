# Smart Car Audio Surveillance Cloud Platform

A comprehensive cloud-based audio surveillance system for smart vehicles that detects and classifies sounds in real-time, generating alerts for critical events.

## 🎯 Overview

This platform provides:
- **Real-time audio ingestion** from IoT devices in vehicles
- **ML-based sound classification** using YAMNet models
- **Automated alert generation** based on configurable rules
- **Web dashboard** for monitoring and managing alerts
- **Cloud-native architecture** using AWS services (S3, SQS, SNS)
- **Scalable microservices** architecture with Docker

## 📦 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  IoT Device │────▶│  Ingestion   │────▶│   S3/SQS    │
│  (Vehicle)  │     │   Service    │     │   Storage   │
└─────────────┘     └──────────────┘     └─────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │  ML Worker     │
                                    │  (YAMNet)      │
                                    └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │  Alert Engine   │
                                    │  (Rules)       │
                                    └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   Dashboard    │
                                    │   (React)      │
                                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (v20.10+)
- Docker Compose (v2.0+)
- AWS Account with:
  - S3 bucket
  - SQS queue
  - SNS topic (optional)
- Git

### Step 1: Clone and Setup

```bash
# Clone the repository
cd "Final project"

# Copy environment template
cp .env.example .env

# Edit .env with your AWS credentials
nano .env
```

### Step 2: Configure AWS

#### Create S3 Bucket
```bash
aws s3 mb s3://smart-car-audio-storage-yourname
```

#### Create SQS Queue
```bash
aws sqs create-queue --queue-name smart-car-audio-queue
# Copy the QueueUrl from the response
```

#### Create SNS Topic (Optional)
```bash
aws sns create-topic --name smart-car-alerts
# Copy the TopicArn from the response

# Subscribe email
aws sns subscribe \
  --topic-arn <your-topic-arn> \
  --protocol email \
  --notification-endpoint your@email.com
```

#### Update .env File
```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2
S3_BUCKET=smart-car-audio-storage-yourname
SQS_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/123456789/smart-car-audio-queue
SNS_TOPIC_ARN=arn:aws:sns:us-west-2:123456789:smart-car-alerts
```

### Step 3: Download Model

Download the YAMNet model from:
- [Model Link](https://drive.google.com/drive/folders/1GBjx2QcLLWtKXeiKAK0iu99Tga3v-wh8)

Place the model file in the `model/` directory. The model file should be named `my_yamnet_human_model_fixed.keras`:

```bash
# The model/ directory should already exist
# Ensure my_yamnet_human_model_fixed.keras is in model/
ls -la model/
```

**Note:** The model file name must match `my_yamnet_human_model_fixed.keras` as configured in docker-compose.yml and the ML worker.

### Step 4: Initialize Database and Create Default Users

After starting services, you need to create default users for login:

```bash
cd backend
python3 -m venv venv  # Create venv if needed
source venv/bin/activate
pip install -r requirements.txt
python scripts/reset_database.py  # Creates default users
```

Or use the quick start script which does this automatically:
```bash
./QUICK_START.sh
```

**Default Login Credentials:**
- Test User: `testing@gmail.com` / `Test@12345`
- Admin User: `deven@gmail.com` / `Deven@123`

### Step 5: Deploy

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup (checks prerequisites, builds, and starts services)
./setup.sh
```

Or manually:

```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f
```

## 📁 Project Structure

```
smart-car-audio-surveillance/
├── backend/
│   ├── services/
│   │   └── audio_ingestion_service.py   # Flask API
│   ├── workers/
│   │   └── ml_inference_worker.py      # ML processing
│   ├── alert_rule_engine.py            # Alert generation
│   ├── ml_interface.py                 # ML utilities
│   ├── requirements.txt                # Python deps
│   └── Dockerfile.*                    # Docker configs
│
├── frontend/
│   └── smartCar/
│       ├── src/
│       │   ├── pages/                  # React pages
│       │   ├── contexts/               # Auth context
│       │   └── App.jsx                # Main app
│       ├── Dockerfile
│       └── package.json
│
├── database/
│   └── schema.sql                      # PostgreSQL schema
│
├── models/                             # ML models directory
├── nginx/
│   └── nginx.conf                      # Reverse proxy
├── docker-compose.yml                  # Orchestration
├── setup.sh                            # Setup script
├── .env.example                        # Environment template
└── README.md                           # This file
```

## 🧪 Testing the System

### 1. Health Check
```bash
curl http://localhost:5001/health
# Should return: {"status": "healthy"}
```

### 2. Initialize Audio Upload
```bash
curl -X POST http://localhost:5001/v1/ingest/audio/init \
  -H "Content-Type: application/json" \
  -d '{
    "carId": "CAR-TEST-001",
    "codec": "wav",
    "sampleRate": 44100,
    "duration": 30.0
  }'
```

### 3. Submit Features
```bash
curl -X POST http://localhost:5001/v1/ingest/features \
  -H "Content-Type: application/json" \
  -d '{
    "carId": "CAR-TEST-001",
    "timestamp": "2025-11-05T14:30:00Z",
    "features": {
      "mfcc": [[0.1, 0.2], [0.3, 0.4]],
      "spectral_centroid": [1500, 1600],
      "zero_crossing_rate": [0.05, 0.06]
    }
  }'
```

### 4. View Alerts
```bash
curl http://localhost:5001/v1/alerts
```

### 5. Access Dashboard
Open browser: http://localhost:3000

**Default Credentials (Created Automatically):**
- **Test User:** `testing@gmail.com` / `Test@12345` (Owner role)
- **Admin User:** `deven@gmail.com` / `Deven@123` (Admin role)

**Note:** These users are automatically created when you run `reset_database.py` or `init_default_users.py`. See `SETUP_INSTRUCTIONS.md` for details.

## 🔌 API Endpoints

### Health
- `GET /health` - Service health check

### Audio Ingestion
- `POST /v1/ingest/audio/init` - Initialize audio upload session
- `POST /v1/ingest/audio/complete` - Complete upload and queue for processing
- `POST /v1/ingest/features` - Submit pre-extracted features

### Alerts
- `GET /v1/alerts` - List alerts (with optional filters)
- `GET /v1/alerts/:id` - Get specific alert
- `POST /v1/alerts/:id/acknowledge` - Acknowledge alert

### Dashboard
- `GET /v1/dashboard/stats` - Get dashboard statistics
- `GET /v1/vehicles` - List vehicles

## 🗄️ Database Schema

The system uses PostgreSQL for relational data:

- **tenant** - Organization/company records
- **users** - User accounts and authentication
- **vehicle** - Vehicle information
- **iot_device** - IoT device metadata
- **ingestion_job** - Audio upload jobs
- **detection** - ML classification results
- **alert** - Generated alerts
- **rule** - Alert rules configuration

See `database/schema.sql` for full schema.

## 🤖 ML Model

The system uses a YAMNet-based model for sound classification:

- **Model**: `my_yamnet_human_model.keras`
- **Labels**: engine_fault, brake_issue, tire_problem, siren, horn, collision, glass_break, human_voice, distress_call, animal_sound, appliance_audio, normal
- **Input**: Audio features (MFCC, spectral centroid, zero crossing rate)
- **Output**: Sound classification with confidence scores

## ⚙️ Configuration

### Alert Rules

Rules are defined in `backend/alert_rule_engine.py`:

```python
RULES = {
    'engine_fault': {
        'threshold': 0.85,
        'severity': 'high',
        'alertType': 'mechanical',
        'notifyOwner': True,
        'notifyService': True,
        'message': 'Engine fault detected...'
    },
    # ... more rules
}
```

### Environment Variables

See `.env.example` for all configuration options.

## 🐳 Docker Services

- **postgres** - PostgreSQL database
- **mongodb** - MongoDB (for future use)
- **redis** - Redis cache
- **ingestion-service** - Flask API service
- **ml-worker** - ML inference worker
- **alert-engine** - Alert processing engine
- **frontend** - React dashboard
- **nginx** - Reverse proxy

## 📊 Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ingestion-service
docker-compose logs -f ml-worker
docker-compose logs -f alert-engine
```

### Service Status
```bash
docker-compose ps
```

### Database Access
```bash
docker-compose exec postgres psql -U smart_car_user -d smart_car_surveillance
```

## 🔧 Troubleshooting

### Services not starting
1. Check Docker is running: `docker ps`
2. Check logs: `docker-compose logs`
3. Verify .env file has correct values
4. Check ports are not in use: `lsof -i :3000 -i :5001 -i :5432`

### Model not loading
1. Verify model file exists: `ls -la models/`
2. Check model path in .env: `MODEL_PATH`
3. Check worker logs: `docker-compose logs ml-worker`

### Database connection errors
1. Wait for database to be ready: `docker-compose ps postgres`
2. Check database health: `docker-compose exec postgres pg_isready`
3. Verify DATABASE_URL in .env

### AWS errors
1. Verify AWS credentials in .env
2. Check S3 bucket exists: `aws s3 ls`
3. Check SQS queue exists: `aws sqs list-queues`
4. Verify IAM permissions

## 🚧 Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
export FLASK_APP=services/audio_ingestion_service.py
flask run --port 5001
```

### Frontend Development
```bash
cd frontend/smartCar
npm install
npm run dev
```

## 📝 License

This project is for educational purposes (CMPE 281 Final Project).

## 👥 Contributors

- Project Team

## 📚 References

- [YAMNet Model](https://github.com/tensorflow/models/tree/master/research/audioset/yamnet)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [React Documentation](https://react.dev/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## 🎓 Project Documentation

See `PROJECT_DOCUMENTATION.md` for detailed implementation guide (if available).

---

**Note**: This is a complete implementation package. Ensure all prerequisites are met and AWS resources are configured before deployment.

