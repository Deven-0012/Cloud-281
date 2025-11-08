"""
Audio Ingestion Service - Smart Car Audio Surveillance Platform
Flask API for receiving audio uploads and feature submissions
"""

import os
import json
import hashlib
import boto3
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
import time

app = Flask(__name__)
CORS(app)

# Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
S3_BUCKET = os.getenv('S3_BUCKET', 'smart-car-audio-storage')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://smart_car_user:SecurePassword123!@postgres:5432/smart_car_surveillance')

# Initialize AWS clients
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)
sqs_client = boto3.client(
    'sqs',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

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
        
        if not data or 'carId' not in data:
            return jsonify({'error': 'Missing required field: carId'}), 400
        
        car_id = data['carId']
        codec = data.get('codec', 'wav')
        sample_rate = data.get('sampleRate', 44100)
        duration = data.get('duration', 30.0)
        channels = data.get('channels', 1)
        
        # Generate S3 key
        timestamp = int(time.time() * 1000)
        s3_key = f"audio/{car_id}/{timestamp}.{codec}"
        
        # Create ingestion job in database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO ingestion_job 
                (vehicle_id, s3_bucket, s3_key, status, sample_rate, channels, duration)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING job_id
            """, (car_id, S3_BUCKET, s3_key, 'pending', sample_rate, channels, duration))
            
            job_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            
            # Generate presigned URL for upload
            presigned_url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': S3_BUCKET,
                    'Key': s3_key,
                    'ContentType': f'audio/{codec}'
                },
                ExpiresIn=3600
            )
            
            return jsonify({
                'jobId': str(job_id),
                's3Key': s3_key,
                'uploadUrl': presigned_url,
                'message': 'Upload session initialized'
            }), 200
            
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/ingest/audio/complete', methods=['POST'])
def complete_audio_upload():
    """
    Complete audio upload and queue for processing
    Expected payload:
    {
        "jobId": "uuid",
        "s3Key": "audio/CAR-A1234/1234567890.wav",
        "checksum": "sha256_hash"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'jobId' not in data or 's3Key' not in data:
            return jsonify({'error': 'Missing required fields: jobId, s3Key'}), 400
        
        job_id = data['jobId']
        s3_key = data['s3Key']
        checksum = data.get('checksum', '')
        
        # Update job status
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get job details
            cur.execute("""
                SELECT vehicle_id, s3_bucket FROM ingestion_job 
                WHERE job_id = %s
            """, (job_id,))
            
            job = cur.fetchone()
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            vehicle_id = job['vehicle_id']
            s3_bucket = job['s3_bucket']
            
            # Update job with checksum and mark as processing
            cur.execute("""
                UPDATE ingestion_job 
                SET status = 'processing', checksum = %s
                WHERE job_id = %s
            """, (checksum, job_id))
            conn.commit()
            
            # Send message to SQS for ML processing
            if SQS_QUEUE_URL:
                message_body = {
                    'carId': vehicle_id,
                    's3Key': s3_key,
                    's3Bucket': s3_bucket,
                    'jobId': str(job_id),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                sqs_client.send_message(
                    QueueUrl=SQS_QUEUE_URL,
                    MessageBody=json.dumps(message_body),
                    MessageAttributes={
                        'ProcessingType': {
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
    app.run(host='0.0.0.0', port=5001, debug=True)

