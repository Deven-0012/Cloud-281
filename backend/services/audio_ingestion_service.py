"""
Audio Ingestion Service - Smart Car Audio Surveillance Platform
Flask API for receiving audio uploads and feature submissions
"""

import os
import json
import hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
import time
import shutil
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configuration
LOCAL_STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'audio_uploads')
DATABASE_URL = os.getenv('DATABASE_URL')

# Create local storage directory if it doesn't exist
os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)

def save_file_locally(file_data, file_path):
    """Save file to local storage"""
    full_path = os.path.join(LOCAL_STORAGE_PATH, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'wb') as f:
        f.write(file_data)
    return full_path

def get_file_url(file_path):
    """Get local file URL"""
    return f"file://{os.path.join(LOCAL_STORAGE_PATH, file_path)}"

# Database connection helper
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'audio-ingestion-service'
    }), 200

@app.route('/v1/ingest/audio/init', methods=['POST'])
def init_audio_upload():
    """
    Initialize audio upload session
    Expected payload:
    {
        "carId": "CAR-A1234",
        "codec": "wav",
        "sampleRate": 44100,
        "duration": 30.0,
        "channels": 1
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        required_fields = ['carId', 'codec', 'sampleRate', 'duration', 'channels']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Generate unique job ID and file path
        job_id = str(uuid.uuid4())
        timestamp = int(time.time())
        file_extension = data['codec'].lower()
        file_path = f"{data['carId']}/{timestamp}.{file_extension}"

        # Create job record in database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ingestion_job (
                        job_id, car_id, status, s3_key, 
                        codec, sample_rate, duration, channels, 
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING job_id, created_at
                """, (
                    job_id, data['carId'], 'uploading', file_path,
                    data['codec'], data['sampleRate'], data['duration'], data['channels']
                ))
                
                result = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    "jobId": result['job_id'],
                    "filePath": file_path,
                    "createdAt": result['created_at'].isoformat()
                }), 200

        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            return jsonify({"error": "Failed to create upload session"}), 500
        finally:
            conn.close()

    except Exception as e:
        print(f"Error in init_audio_upload: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """
    Handle direct file upload
    Expected form data:
    - file: The audio file
    - carId: Vehicle ID
    - codec: Audio codec (e.g., wav, mp3)
    - sampleRate: Sample rate in Hz
    - duration: Duration in seconds
    - channels: Number of audio channels
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        # Get form data
        car_id = request.form.get('carId')
        codec = request.form.get('codec', 'wav')
        sample_rate = request.form.get('sampleRate', 44100, type=int)
        duration = request.form.get('duration', 0, type=float)
        channels = request.form.get('channels', 1, type=int)
        
        # Generate unique file path
        timestamp = int(time.time())
        file_extension = codec.lower()
        file_path = f"{car_id}/{timestamp}.{file_extension}"
        
        # Save file locally
        file_data = file.read()
        save_file_locally(file_data, file_path)
        
        # Create job record in database
        job_id = str(uuid.uuid4())
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ingestion_job (
                        job_id, car_id, status, s3_key, 
                        codec, sample_rate, duration, channels, 
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING job_id, created_at
                """, (
                    job_id, car_id, 'pending', file_path,
                    codec, sample_rate, duration, channels
                ))
                
                result = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    "jobId": result['job_id'],
                    "filePath": file_path,
                    "createdAt": result['created_at'].isoformat()
                }), 200
                
        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            return jsonify({"error": "Failed to process upload"}), 500
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error in upload_audio: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/upload/complete', methods=['POST'])
def complete_audio_upload():
    """
    Complete audio upload and queue for processing
    Expected payload:
    {
        "jobId": "uuid",
        "filePath": "CAR-A1234/1234567890.wav",
        "checksum": "sha256_hash"
    }
    """
    try:
        data = request.get_json()
        if not data or 'jobId' not in data or 'filePath' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        job_id = data['jobId']
        file_path = data['filePath']
        checksum = data.get('checksum')

        # Update job status in database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        try:
            with conn.cursor() as cur:
                # Update job status to processing
                cur.execute("""
                    UPDATE ingestion_job 
                    SET status = 'processing', 
                        s3_key = %s,
                        checksum = %s,
                        updated_at = NOW()
                    WHERE job_id = %s
                    RETURNING job_id, car_id, status
                """, (file_path, checksum, job_id))
                
                result = cur.fetchone()
                if not result:
                    return jsonify({"error": "Job not found"}), 404
                    
                conn.commit()
                
                # In a real implementation, you would queue the job for ML processing here
                # For local development, we'll just update the status to completed
                cur.execute("""
                    UPDATE ingestion_job 
                    SET status = 'completed', 
                        updated_at = NOW()
                    WHERE job_id = %s
                """, (job_id,))
                conn.commit()
                
                return jsonify({
                    "jobId": result['job_id'],
                    "status": "completed",
                    "filePath": file_path
                }), 200
                
        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            return jsonify({"error": "Failed to process upload completion"}), 500
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error in complete_audio_upload: {e}")
        return jsonify({"error": "Internal server error"}), 500
                # Local processing complete
                print(f"Job {job_id} marked as completed for file: {file_path}")
                            'DataType': 'String',
                            'StringValue': 'audio'
                        },
                        'JobId': {
                            'DataType': 'String',
                            'StringValue': str(job_id)
                        }
                    }
                )
            
            cur.close()
            
            return jsonify({
                'jobId': str(job_id),
                'status': 'queued',
                'message': 'Audio uploaded and queued for processing'
            }), 200
            
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/ingest/features', methods=['POST'])
def ingest_features():
    """
    Submit pre-extracted audio features for classification
    Expected payload:
    {
        "carId": "CAR-A1234",
        "timestamp": "2025-11-05T14:30:00Z",
        "features": {
            "mfcc": [[0.1, 0.2], [0.3, 0.4]],
            "spectral_centroid": [1500, 1600],
            "zero_crossing_rate": [0.05, 0.06]
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'carId' not in data or 'features' not in data:
            return jsonify({'error': 'Missing required fields: carId, features'}), 400
        
        car_id = data['carId']
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        features = data['features']
        
        # Send message to SQS for ML processing
        if SQS_QUEUE_URL:
            message_body = {
                'carId': car_id,
                'timestamp': timestamp,
                'features': features
            }
            
            sqs_client.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    'ProcessingType': {
                        'DataType': 'String',
                        'StringValue': 'features'
                    }
                }
            )
        
        return jsonify({
            'status': 'queued',
            'message': 'Features queued for processing',
            'carId': car_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/alerts', methods=['GET'])
def get_alerts():
    """Get alerts with optional filtering"""
    try:
        status = request.args.get('status', 'new')
        vehicle_id = request.args.get('vehicleId')
        limit = int(request.args.get('limit', 50))
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM alert WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = %s"
                params.append(status)
            
            if vehicle_id:
                query += " AND vehicle_id = %s"
                params.append(vehicle_id)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            alerts = cur.fetchall()
            
            # Convert to JSON-serializable format
            result = []
            for alert in alerts:
                alert_dict = dict(alert)
                if alert_dict.get('confidence'):
                    alert_dict['confidence'] = float(alert_dict['confidence'])
                if alert_dict.get('location'):
                    alert_dict['location'] = {'x': alert_dict['location'][0], 'y': alert_dict['location'][1]}
                result.append(alert_dict)
            
            cur.close()
            
            return jsonify({
                'alerts': result,
                'count': len(result)
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/alerts/<alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get specific alert by ID"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM alert WHERE alert_id = %s", (alert_id,))
            alert = cur.fetchone()
            
            if not alert:
                return jsonify({'error': 'Alert not found'}), 404
            
            alert_dict = dict(alert)
            if alert_dict.get('confidence'):
                alert_dict['confidence'] = float(alert_dict['confidence'])
            
            cur.close()
            
            return jsonify(alert_dict), 200
            
        except Exception as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        data = request.get_json() or {}
        user_id = data.get('userId')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE alert 
                SET status = 'acknowledged', 
                    acknowledged_at = CURRENT_TIMESTAMP,
                    acknowledged_by = %s
                WHERE alert_id = %s
                RETURNING alert_id
            """, (user_id, alert_id))
            
            if cur.fetchone():
                conn.commit()
                cur.close()
                return jsonify({'message': 'Alert acknowledged', 'alertId': alert_id}), 200
            else:
                return jsonify({'error': 'Alert not found'}), 404
                
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/vehicles', methods=['GET'])
def get_vehicles():
    """Get list of vehicles"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM vehicle ORDER BY created_at DESC")
            vehicles = cur.fetchall()
            cur.close()
            
            return jsonify({
                'vehicles': [dict(v) for v in vehicles],
                'count': len(vehicles)
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get vehicle counts
            cur.execute("SELECT COUNT(*) as total, status FROM vehicle GROUP BY status")
            vehicles_by_status = {row['status']: row['total'] for row in cur.fetchall()}
            
            # Get alert counts
            cur.execute("""
                SELECT COUNT(*) as total, status 
                FROM alert 
                WHERE status IN ('new', 'under_review')
                GROUP BY status
            """)
            alerts_by_status = {row['status']: row['total'] for row in cur.fetchall()}
            
            # Get alert counts by type
            cur.execute("""
                SELECT COUNT(*) as total, alert_type 
                FROM alert 
                WHERE status IN ('new', 'under_review')
                GROUP BY alert_type
            """)
            alerts_by_type = {row['alert_type']: row['total'] for row in cur.fetchall()}
            
            # Get device counts
            cur.execute("SELECT COUNT(*) as total FROM iot_device")
            device_count = cur.fetchone()['total']
            
            cur.close()
            
            return jsonify({
                'connectedCars': vehicles_by_status.get('active', 0),
                'onlineCars': vehicles_by_status.get('active', 0),
                'offlineCars': vehicles_by_status.get('inactive', 0),
                'activeAlerts': sum(alerts_by_status.values()),
                'emergencyAlerts': alerts_by_type.get('emergency', 0),
                'safetyAlerts': alerts_by_type.get('safety', 0),
                'anomalyAlerts': alerts_by_type.get('maintenance', 0),
                'iotDevices': device_count,
                'microphones': device_count,  # Simplified
                'cameras': 0
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
