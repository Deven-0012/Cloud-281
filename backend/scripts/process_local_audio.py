#!/usr/bin/env python3
"""
Script to process local audio files from audio_uploads folder
This script simulates the complete flow:
1. Reads audio files from audio_uploads
2. Processes them through ML model
3. Generates alerts with criticality levels
4. Stores in database

Usage:
    # Activate virtual environment first:
    source ../venv/bin/activate
    
    # Then run:
    python scripts/process_local_audio.py
"""

import os
import sys
import time
from pathlib import Path

# Check if running in virtual environment
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'venv')
    if os.path.exists(venv_path):
        print("="*60)
        print("WARNING: Virtual environment not activated!")
        print("="*60)
        print(f"Please activate the virtual environment first:")
        print(f"  cd {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
        print(f"  source venv/bin/activate")
        print(f"  python scripts/process_local_audio.py")
        print("="*60)
        sys.exit(1)
    else:
        print("WARNING: No virtual environment found. Make sure dependencies are installed.")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from workers.ml_inference_worker import process_audio_file_local
    from services.alert_rule_engine import process_detection
except ImportError as e:
    print("="*60)
    print("ERROR: Missing required dependencies!")
    print("="*60)
    print(f"Error: {e}")
    print("\nPlease install dependencies:")
    print("  cd backend")
    print("  source venv/bin/activate")
    print("  pip install -r requirements.txt")
    print("="*60)
    sys.exit(1)

# Configuration
AUDIO_UPLOADS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'audio_uploads')
SUPPORTED_FORMATS = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']

def find_audio_files(base_path):
    """Find all audio files in the directory structure"""
    audio_files = []
    base = Path(base_path)
    
    if not base.exists():
        print(f"Error: Audio uploads directory not found: {base_path}")
        return []
    
    for ext in SUPPORTED_FORMATS:
        audio_files.extend(base.rglob(f'*{ext}'))
        audio_files.extend(base.rglob(f'*{ext.upper()}'))
    
    return sorted(audio_files)

def extract_vehicle_id(file_path):
    """Extract vehicle/user ID from file path (e.g., audio_uploads/User1/file.wav or audio_uploads/Ford_car/file.wav)"""
    path_obj = Path(file_path)
    parts = path_obj.parts
    
    # Find the index of 'audio_uploads' in the path
    try:
        audio_uploads_idx = parts.index('audio_uploads')
        # The vehicle/user ID should be the next part after 'audio_uploads'
        if audio_uploads_idx + 1 < len(parts):
            vehicle_id = parts[audio_uploads_idx + 1]
            # Make sure it's not a file (has extension)
            if not any(vehicle_id.endswith(ext) for ext in ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.WAV', '.MP3', '.M4A']):
                return vehicle_id
    except ValueError:
        pass
    
    # Fallback: look for any directory name that's not a common path component
    for part in parts:
        # Skip common directory names and files
        if part in ['audio_uploads', 'backend', 'Cloud-281', 'Final_Final', '281', 'Users', 'devendesai']:
            continue
        # Skip if it's a file (has audio extension)
        if any(part.endswith(ext) for ext in ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.WAV', '.MP3', '.M4A']):
            continue
        # Skip if it's a root path component
        if part == '/' or part == '':
            continue
        # Use the first valid directory name found
        return part
    
    # Default vehicle ID if not found in path
    return 'UNKNOWN-VEHICLE'

def ensure_vehicle_exists(vehicle_id, user_email=None, user_id=None):
    """Ensure vehicle exists in database, create if it doesn't
    
    Args:
        vehicle_id: Vehicle/user ID (e.g., User1, Ford_car)
        user_email: Optional email to link vehicle to specific user
        user_id: Optional user_id to link vehicle to specific user
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import os
    
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://smart_car_user:SecurePassword123!@127.0.0.1:5433/smart_car_surveillance')
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if vehicle exists
        cur.execute("SELECT vehicle_id, owner_id FROM vehicle WHERE vehicle_id = %s", (vehicle_id,))
        existing = cur.fetchone()
        
        if existing:
            # Vehicle exists - update owner if user_email/user_id provided
            if user_email or user_id:
                owner_id_to_use = None
                if user_id:
                    owner_id_to_use = user_id
                elif user_email:
                    cur.execute("SELECT user_id FROM users WHERE email = %s", (user_email,))
                    user_result = cur.fetchone()
                    if user_result:
                        owner_id_to_use = user_result['user_id']
                
                if owner_id_to_use and existing['owner_id'] != owner_id_to_use:
                    cur.execute("""
                        UPDATE vehicle SET owner_id = %s WHERE vehicle_id = %s
                    """, (owner_id_to_use, vehicle_id))
                    conn.commit()
                    print(f"✓ Updated vehicle {vehicle_id} owner to user")
            
            cur.close()
            conn.close()
            return True
        
        # Create vehicle if it doesn't exist
        owner_id = None
        
        # Try to get owner from provided user_email or user_id
        if user_id:
            owner_id = user_id
        elif user_email:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (user_email,))
            user_result = cur.fetchone()
            if user_result:
                owner_id = user_result['user_id']
        
        # If no owner specified, default to testing@gmail.com (the test user)
        if not owner_id:
            cur.execute("SELECT user_id FROM users WHERE email = 'testing@gmail.com'")
            test_user_result = cur.fetchone()
            if test_user_result:
                owner_id = test_user_result['user_id']
                print(f"  → Auto-assigning vehicle {vehicle_id} to testing@gmail.com (default test user)")
            else:
                print(f"⚠ Warning: No owner specified and test user not found. Vehicle will be created without owner.")
                owner_id = None
        
        # Only insert if owner_id is provided
        if owner_id:
            cur.execute("""
                INSERT INTO vehicle (vehicle_id, owner_id, make, model, license_plate, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (vehicle_id) DO UPDATE SET owner_id = COALESCE(EXCLUDED.owner_id, vehicle.owner_id)
            """, (vehicle_id, owner_id, 'Unknown', 'Unknown', vehicle_id, 'active'))
        else:
            # Create vehicle without owner (must be assigned later)
            cur.execute("""
                INSERT INTO vehicle (vehicle_id, owner_id, make, model, license_plate, status, created_at)
                VALUES (%s, NULL, %s, %s, %s, %s, NOW())
                ON CONFLICT (vehicle_id) DO NOTHING
            """, (vehicle_id, 'Unknown', 'Unknown', vehicle_id, 'active'))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✓ Created vehicle record: {vehicle_id} (owner: {owner_id})")
        return True
    except Exception as e:
        print(f"Warning: Could not ensure vehicle exists: {e}")
        return False

def process_audio_file(file_path, vehicle_id=None, user_email=None, user_id=None):
    """Process a single audio file through the complete pipeline
    
    Args:
        file_path: Path to audio file
        vehicle_id: Optional vehicle ID (extracted from path if not provided)
        user_email: Optional user email to link vehicle to specific user
        user_id: Optional user_id to link vehicle to specific user
    """
    if vehicle_id is None:
        vehicle_id = extract_vehicle_id(file_path)
    
    print(f"\n{'='*60}")
    print(f"Processing: {file_path}")
    print(f"User/Vehicle ID: {vehicle_id}")
    if user_email:
        print(f"Linking to user: {user_email}")
    print(f"{'='*60}")
    
    # Ensure vehicle exists in database and link to user if provided
    ensure_vehicle_exists(vehicle_id, user_email=user_email, user_id=user_id)
    
    try:
        # Process through ML worker
        detection = process_audio_file_local(str(file_path), vehicle_id)
        
        if detection:
            print(f"✓ Detection created: {detection['soundLabel']} (confidence: {detection['confidence']:.2%})")
            
            # Process through alert engine
            alert = process_detection(detection)
            
            if alert:
                priority = alert.get('priority', 'medium')
                severity = alert.get('severity', 'medium')
                print(f"✓ Alert created: {alert['alertId']}")
                print(f"  Type: {alert['alertType']}")
                print(f"  Severity: {severity}")
                print(f"  Priority: {priority}")
                print(f"  Message: {alert['message']}")
                return True
            else:
                print(f"⚠ No alert generated (confidence below threshold or duplicate)")
                return False
        else:
            print(f"✗ Failed to process audio file")
            return False
            
    except Exception as e:
        print(f"✗ Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to process all audio files"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process local audio files')
    parser.add_argument('--user-email', help='Email of user to link vehicles to (REQUIRED for proper ownership)')
    parser.add_argument('--user-id', help='User ID to link vehicles to')
    args = parser.parse_args()
    
    print("="*60)
    print("Audio Anomaly Detection - Local File Processor")
    print("="*60)
    print(f"Scanning directory: {AUDIO_UPLOADS_PATH}")
    
    if not args.user_email and not args.user_id:
        print("\nℹ No user specified - will default to testing@gmail.com (test user)")
        print("   All vehicles and alerts will be linked to testing@gmail.com")
    
    if args.user_email:
        print(f"Linking vehicles to user: {args.user_email}")
    if args.user_id:
        print(f"Linking vehicles to user ID: {args.user_id}")
    
    audio_files = find_audio_files(AUDIO_UPLOADS_PATH)
    
    if not audio_files:
        print(f"\nNo audio files found in {AUDIO_UPLOADS_PATH}")
        print("Supported formats:", ', '.join(SUPPORTED_FORMATS))
        return
    
    print(f"\nFound {len(audio_files)} audio file(s) to process\n")
    
    success_count = 0
    alert_count = 0
    
    for i, file_path in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}]")
        result = process_audio_file(
            file_path, 
            user_email=args.user_email,
            user_id=args.user_id
        )
        
        if result:
            success_count += 1
            alert_count += 1
        else:
            success_count += 1  # Still counts as processed even if no alert
        
        # Small delay between files
        if i < len(audio_files):
            time.sleep(1)
    
    print("\n" + "="*60)
    print("Processing Complete")
    print("="*60)
    print(f"Files processed: {success_count}/{len(audio_files)}")
    print(f"Alerts generated: {alert_count}")
    print("\nCheck the dashboard to see the results!")
    if args.user_email:
        print(f"\nNote: Alerts are linked to user: {args.user_email}")
        print("Make sure you're logged in with this email to see the alerts!")

if __name__ == '__main__':
    main()

