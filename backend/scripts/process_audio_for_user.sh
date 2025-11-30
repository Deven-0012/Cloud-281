#!/bin/bash
# Wrapper script to process audio files for a specific user
# Usage: ./process_audio_for_user.sh user@example.com

if [ -z "$1" ]; then
    echo "Usage: $0 <user_email>"
    echo "Example: $0 user@example.com"
    exit 1
fi

USER_EMAIL="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$BACKEND_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export DATABASE_URL="${DATABASE_URL:-postgresql://smart_car_user:SecurePassword123!@127.0.0.1:5433/smart_car_surveillance}"
export MODEL_PATH="${MODEL_PATH:-$BACKEND_DIR/../model/my_yamnet_human_model_fixed.keras}"
export LOCAL_MODE="true"

echo "Processing audio files for user: $USER_EMAIL"
python scripts/process_local_audio.py --user-email "$USER_EMAIL"

