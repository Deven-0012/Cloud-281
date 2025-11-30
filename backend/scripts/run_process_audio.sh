#!/bin/bash
# Wrapper script to process local audio files with proper environment setup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import tensorflow_hub" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Set environment variables
export DATABASE_URL="${DATABASE_URL:-postgresql://smart_car_user:SecurePassword123!@127.0.0.1:5433/smart_car_surveillance}"
export MODEL_PATH="${MODEL_PATH:-$PROJECT_ROOT/model/my_yamnet_human_model_fixed.keras}"
export LOCAL_MODE="true"

# Check if model file exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "Warning: Model file not found at $MODEL_PATH"
    echo "Please set MODEL_PATH environment variable or place model at: $PROJECT_ROOT/model/my_yamnet_human_model_fixed.keras"
fi

# Check database connection
echo "Checking database connection..."
if ! python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; then
    echo "Warning: Cannot connect to database at $DATABASE_URL"
    echo "Make sure PostgreSQL is running and accessible."
fi

# Run the script
echo "Processing audio files..."
echo "Using MODEL_PATH: $MODEL_PATH"
echo "Using DATABASE_URL: $DATABASE_URL"
echo ""
echo "NOTE: All vehicles will be linked to testing@gmail.com (default test user)"
echo "      To use a different user, run: ./scripts/process_audio_for_user.sh user@example.com"
echo ""
python scripts/process_local_audio.py

