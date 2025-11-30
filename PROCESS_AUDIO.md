# Audio Anomaly Detection - Processing Guide

This guide explains how to process local audio files and see the complete flow from audio upload to alert generation.

## Complete Flow

1. **Audio Upload** → Audio files are stored in `backend/audio_uploads/`
2. **ML Processing** → YAMNet model extracts features and classifies sounds
3. **Alert Generation** → Alert rule engine evaluates detections and creates alerts with priority levels
4. **Dashboard Display** → Frontend shows real-time updates with anomaly counts and criticality

## Processing Audio Files

### Option 1: Using the Processing Script

**Method A: Using the wrapper script (Recommended)**

```bash
cd /Users/devendesai/281/Final_Final/Cloud-281/backend
./scripts/run_process_audio.sh
```

**Method B: Manual activation**

```bash
cd /Users/devendesai/281/Final_Final/Cloud-281/backend
source venv/bin/activate
python scripts/process_local_audio.py
```

**Note:** Make sure the virtual environment is activated and dependencies are installed:
```bash
pip install -r requirements.txt
```

This will:
- Find all audio files in `audio_uploads/`
- Process each through the ML model
- Generate alerts based on confidence thresholds
- Store detections and alerts in the database

### Option 2: Using the API Endpoint

You can process a specific audio file via API:

```bash
curl -X POST http://localhost:5001/v1/test/process-audio \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "filePath": "CAR-A1234/1763163317.wav",
    "vehicleId": "CAR-A1234"
  }'
```

### Option 3: Upload via API

Use the upload endpoints to upload new audio files:

```bash
# 1. Initialize upload
curl -X POST http://localhost:5001/v1/ingest/audio/init \
  -H "Content-Type: application/json" \
  -d '{
    "carId": "CAR-A1234",
    "codec": "wav",
    "sampleRate": 44100,
    "duration": 30.0,
    "channels": 1
  }'

# 2. Upload file (multipart/form-data)
curl -X POST http://localhost:5001/api/upload \
  -F "file=@/path/to/audio.wav" \
  -F "carId=CAR-A1234" \
  -F "codec=wav" \
  -F "sampleRate=44100" \
  -F "duration=30.0" \
  -F "channels=1"

# 3. Complete upload (triggers processing)
curl -X POST http://localhost:5001/api/upload/complete \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": "JOB_ID_FROM_STEP_1",
    "filePath": "CAR-A1234/timestamp.wav"
  }'
```

## Alert Priority Levels

Alerts are classified by priority based on severity:

- **High Priority**: `critical` or `high` severity
- **Medium Priority**: `medium` severity  
- **Low Priority**: `low` severity

### Sound Classification Rules

| Sound Type | Threshold | Severity | Priority | Alert Type |
|------------|-----------|----------|----------|------------|
| engine_fault | 0.85 | high | High | mechanical |
| brake_issue | 0.80 | critical | High | safety |
| tire_problem | 0.75 | medium | Medium | maintenance |
| siren | 0.90 | high | High | emergency |
| collision | 0.85 | critical | High | emergency |
| glass_break | 0.80 | high | High | security |
| distress_call | 0.85 | critical | High | emergency |

## Viewing Results

### Dashboard
- Open the frontend at `http://localhost:5173`
- Login with your account
- The dashboard shows:
  - **Active Alerts**: Total count with priority breakdown (High/Medium/Low)
  - **Live Safety Feed**: Recent alerts with sound classifications
  - **Fleet Overview**: Connected vehicles and their status

### Alerts Page
- Navigate to "Live Map" to see:
  - Alert locations on map
  - Alert details with priority levels
  - Filter by type, confidence, and time

### Real-time Updates
- Dashboard refreshes every 5 seconds
- Alerts page refreshes every 30 seconds
- New alerts appear automatically

## Troubleshooting

### No alerts generated?
1. Check if confidence meets threshold (see rules above)
2. Verify audio file was processed (check detection table)
3. Check alert_rule_engine logs for processing errors

### Database connection issues?
1. Ensure PostgreSQL is running: `docker ps | grep postgres`
2. Check DATABASE_URL environment variable
3. Verify port 5433 is accessible

### ML model not loading?
1. Verify MODEL_PATH points to correct model file
2. Check model file exists: `ls -la model/my_yamnet_human_model_fixed.keras`
3. Review ML worker logs for errors

## Testing the Complete Flow

1. **Start all services** (using `start-all.sh` or manually)
2. **Process audio files**: Run `python backend/scripts/process_local_audio.py`
3. **Check dashboard**: Open frontend and verify alerts appear
4. **Verify priority**: Check that alerts show correct priority levels
5. **Test real-time**: Process another file and watch dashboard update

## Next Steps

- Add WebSocket support for instant updates
- Implement alert acknowledgment
- Add alert filtering by priority
- Create alert history view
- Add sound classification visualization

