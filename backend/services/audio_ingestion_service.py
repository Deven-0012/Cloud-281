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
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import bcrypt
from functools import wraps
import jwt

app = Flask(__name__)
# Enable CORS for all routes and origins (for development/tunneling)
# This allows requests from any origin, including tunnels
CORS(app, 
     resources={r"/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
)

# Configuration
LOCAL_STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'audio_uploads')
DATABASE_URL = os.getenv('DATABASE_URL')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL', '')
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')

# Local processing mode (no AWS)
LOCAL_MODE = os.getenv('LOCAL_MODE', 'true').lower() == 'true'

# Initialize AWS clients with error handling
sqs_client = None
if SQS_QUEUE_URL:
    try:
        # Validate AWS credentials
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if not aws_access_key or not aws_secret_key:
            print("Warning: AWS credentials not found. SQS functionality will be disabled.")
        else:
            sqs_client = boto3.client('sqs', 
                                     region_name=AWS_REGION,
                                     aws_access_key_id=aws_access_key,
                                     aws_secret_access_key=aws_secret_key)
            print(f"SQS client initialized for queue: {SQS_QUEUE_URL}")
    except (NoCredentialsError, ClientError) as e:
        print(f"Warning: Failed to initialize SQS client: {e}")
        sqs_client = None

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

# Database connection helper with retry logic
def get_db_connection(max_retries=3):
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable is not set")
        return None
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Database connection attempt {attempt + 1} failed, retrying...")
                time.sleep(1)
            else:
                print(f"Database connection error after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            print(f"Unexpected database connection error: {e}")
            return None
    return None

# Authentication helpers
def generate_token(user_id, email, role):
    """Generate JWT token for user"""
    payload = {
        'user_id': str(user_id),
        'email': email,
        'role': role,
        'exp': datetime.utcnow().timestamp() + (24 * 60 * 60)  # 24 hours
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.user = payload
        return f(*args, **kwargs)
    return decorated_function

def require_role(*allowed_roles):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            if request.user.get('role') not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'audio-ingestion-service',
        'local_mode': LOCAL_MODE
    }), 200

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS,PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Authentication endpoints
@app.route('/v1/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email']
        password = data['password']
        full_name = data.get('full_name', '')
        role = data.get('role', 'owner')  # owner, admin
        
        if role not in ['owner', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor()
            # Check if user exists
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({'error': 'User already exists'}), 400
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Get default tenant (or create one)
            cur.execute("SELECT tenant_id FROM tenant LIMIT 1")
            tenant_row = cur.fetchone()
            if not tenant_row:
                # Create default tenant
                tenant_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO tenant (tenant_id, name, email)
                    VALUES (%s, %s, %s)
                """, (tenant_id, 'Default Tenant', email))
            else:
                tenant_id = tenant_row[0]
            
            # Create user
            user_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO users (user_id, tenant_id, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING user_id, email, full_name, role
            """, (user_id, tenant_id, email, password_hash, full_name, role))
            
            user = cur.fetchone()
            conn.commit()
            cur.close()
            
            # Generate token
            token = generate_token(user_id, email, role)
            
            return jsonify({
                'token': token,
                'user': {
                    'user_id': user[0],
                    'email': user[1],
                    'full_name': user[2],
                    'role': user[3]
                }
            }), 201
            
        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            return jsonify({'error': 'Failed to create user'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error in register: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/v1/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email']
        password = data['password']
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT user_id, email, password_hash, full_name, role
                FROM users WHERE email = %s
            """, (email,))
            
            user = cur.fetchone()
            if not user:
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Update last login
            cur.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (user['user_id'],))
            conn.commit()
            cur.close()
            
            # Generate token
            token = generate_token(user['user_id'], user['email'], user['role'])
            
            return jsonify({
                'token': token,
                'user': {
                    'user_id': str(user['user_id']),
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'role': user['role']
                }
            }), 200
            
        except Exception as e:
            print(f"Database error: {e}")
            return jsonify({'error': 'Login failed'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error in login: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/v1/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user info"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT user_id, email, full_name, role, tenant_id
                FROM users WHERE user_id = %s
            """, (request.user['user_id'],))
            
            user = cur.fetchone()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            cur.close()
            
            return jsonify({
                'user': {
                    'user_id': str(user['user_id']),
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'role': user['role'],
                    'tenant_id': str(user['tenant_id']) if user['tenant_id'] else None
                }
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
                        job_id, vehicle_id, status, s3_key, 
                        duration, sample_rate, channels, 
                        created_at, processed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NULL)
                    RETURNING job_id, created_at
                """, (
                    job_id, data['carId'], 'pending', file_path,
                    data['duration'], data['sampleRate'], data['channels']
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
                        job_id, vehicle_id, status, s3_key, 
                        duration, sample_rate, channels, 
                        created_at, processed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NULL)
                    RETURNING job_id, created_at
                """, (
                    job_id, car_id, 'pending', file_path,
                    duration, sample_rate, channels
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
                        checksum = %s
                    WHERE job_id = %s
                    RETURNING job_id, vehicle_id, status
                """, (file_path, checksum, job_id))
                
                result = cur.fetchone()
                if not result:
                    return jsonify({"error": "Job not found"}), 404
                    
                conn.commit()
                
                # Process locally or queue to SQS
                if LOCAL_MODE or not sqs_client:
                    # Local processing - trigger ML worker directly
                    try:
                        from workers.ml_inference_worker import process_audio_file_local
                        local_file_path = os.path.join(LOCAL_STORAGE_PATH, file_path)
                        if os.path.exists(local_file_path):
                            # Process in background (in production, use a task queue)
                            import threading
                            thread = threading.Thread(
                                target=process_audio_file_local,
                                args=(local_file_path, result['vehicle_id'], job_id)
                            )
                            thread.daemon = True
                            thread.start()
                            print(f"Job {job_id} processing locally")
                        else:
                            print(f"Warning: Local file not found: {local_file_path}")
                    except ImportError:
                        print("Warning: ML worker not available for local processing")
                    except Exception as e:
                        print(f"Error starting local processing: {e}")
                elif sqs_client and SQS_QUEUE_URL:
                    # Queue to SQS
                    try:
                        message_body = {
                            'jobId': str(job_id),
                            'carId': result['vehicle_id'],
                            's3Key': file_path,
                            's3Bucket': os.getenv('S3_BUCKET', 'smart-car-audio-storage')
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
                        print(f"Job {job_id} queued for ML processing")
                    except Exception as sqs_error:
                        print(f"Warning: Failed to queue job to SQS: {sqs_error}")
                
                return jsonify({
                    "jobId": result['job_id'],
                    "status": "processing",
                    "filePath": file_path,
                    "message": "Audio uploaded and processing"
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
        if sqs_client and SQS_QUEUE_URL:
            try:
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
            except Exception as sqs_error:
                print(f"Warning: Failed to send features to SQS: {sqs_error}")
                return jsonify({'error': 'Failed to queue features for processing'}), 500
        
        return jsonify({
            'status': 'queued',
            'message': 'Features queued for processing',
            'carId': car_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/alerts', methods=['GET'])
@require_auth
def get_alerts():
    """Get alerts with optional filtering - role-based access"""
    try:
        status = request.args.get('status', 'new')
        vehicle_id = request.args.get('vehicleId')
        limit = int(request.args.get('limit', 50))
        user_role = request.user.get('role')
        user_id = request.user.get('user_id')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build query based on role
            if user_role == 'admin':
                # Admin can see all alerts
                query = """
                    SELECT a.*, v.make, v.model, v.license_plate
                    FROM alert a
                    LEFT JOIN vehicle v ON a.vehicle_id = v.vehicle_id
                    WHERE 1=1
                """
                params = []
            else:
                # Owners can ONLY see alerts for their own vehicles (strict filtering)
                # Must have owner_id set and match the current user
                query = """
                    SELECT a.*, v.make, v.model, v.license_plate
                    FROM alert a
                    INNER JOIN vehicle v ON a.vehicle_id = v.vehicle_id
                    WHERE v.owner_id = %s AND v.owner_id IS NOT NULL
                """
                params = [user_id]
            
            if status:
                query += " AND a.status = %s"
                params.append(status)
            
            if vehicle_id:
                query += " AND a.vehicle_id = %s"
                params.append(vehicle_id)
            
            query += " ORDER BY a.created_at DESC LIMIT %s"
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
                    # Handle POINT type
                    if isinstance(alert_dict['location'], tuple):
                        alert_dict['location'] = {'lat': float(alert_dict['location'][0]), 'lng': float(alert_dict['location'][1])}
                    elif alert_dict['location']:
                        # If it's a string like "(lat,lng)"
                        loc_str = str(alert_dict['location']).strip('()')
                        parts = loc_str.split(',')
                        if len(parts) == 2:
                            alert_dict['location'] = {'lat': float(parts[0]), 'lng': float(parts[1])}
                
                # Map severity to priority
                severity = alert_dict.get('severity', 'medium')
                if severity == 'critical':
                    alert_dict['priority'] = 'high'
                elif severity == 'high':
                    alert_dict['priority'] = 'high'
                elif severity == 'medium':
                    alert_dict['priority'] = 'medium'
                else:
                    alert_dict['priority'] = 'low'
                
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
@require_auth
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        user_id = request.user.get('user_id')
        
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

@app.route('/v1/alerts/<alert_id>', methods=['DELETE'])
@require_auth
def delete_alert(alert_id):
    """Delete an alert - Admin only"""
    try:
        user_role = request.user.get('role')
        
        # Only admins can delete alerts
        if user_role != 'admin':
            return jsonify({'error': 'Insufficient permissions. Only admins can delete alerts.'}), 403
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor()
            # Check if alert exists
            cur.execute("SELECT alert_id FROM alert WHERE alert_id = %s", (alert_id,))
            if not cur.fetchone():
                cur.close()
                return jsonify({'error': 'Alert not found'}), 404
            
            # Delete the alert
            cur.execute("DELETE FROM alert WHERE alert_id = %s RETURNING alert_id", (alert_id,))
            deleted = cur.fetchone()
            
            if deleted:
                conn.commit()
                cur.close()
                return jsonify({'message': 'Alert deleted successfully', 'alertId': alert_id}), 200
            else:
                conn.rollback()
                cur.close()
                return jsonify({'error': 'Failed to delete alert'}), 500
                
        except Exception as e:
            conn.rollback()
            print(f"Error deleting alert: {e}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/vehicles', methods=['GET'])
@require_auth
def get_vehicles():
    """Get list of vehicles - role-based access"""
    try:
        user_role = request.user.get('role')
        user_id = request.user.get('user_id')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Admin can see all vehicles, users only their own
            if user_role == 'admin':
                cur.execute("""
                    SELECT v.*, 
                           COUNT(DISTINCT a.alert_id) as alert_count,
                           COUNT(DISTINCT CASE WHEN a.status = 'new' THEN a.alert_id END) as new_alert_count
                    FROM vehicle v
                    LEFT JOIN alert a ON v.vehicle_id = a.vehicle_id
                    GROUP BY v.vehicle_id
                    ORDER BY v.created_at DESC
                """)
            else:
                cur.execute("""
                    SELECT v.*, 
                           COUNT(DISTINCT a.alert_id) as alert_count,
                           COUNT(DISTINCT CASE WHEN a.status = 'new' THEN a.alert_id END) as new_alert_count
                    FROM vehicle v
                    LEFT JOIN alert a ON v.vehicle_id = a.vehicle_id
                    WHERE v.owner_id = %s AND v.owner_id IS NOT NULL
                    GROUP BY v.vehicle_id
                    ORDER BY v.created_at DESC
                """, (user_id,))
            
            vehicles = cur.fetchall()
            cur.close()
            
            result = []
            for v in vehicles:
                vehicle_dict = dict(v)
                # Get latest alert location for map
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("""
                    SELECT location, created_at
                    FROM alert
                    WHERE vehicle_id = %s AND location IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (vehicle_dict['vehicle_id'],))
                latest_alert = cur.fetchone()
                cur.close()
                
                if latest_alert and latest_alert['location']:
                    if isinstance(latest_alert['location'], tuple):
                        vehicle_dict['last_alert_location'] = {
                            'lat': float(latest_alert['location'][0]),
                            'lng': float(latest_alert['location'][1])
                        }
                    else:
                        loc_str = str(latest_alert['location']).strip('()')
                        parts = loc_str.split(',')
                        if len(parts) == 2:
                            vehicle_dict['last_alert_location'] = {
                                'lat': float(parts[0]),
                                'lng': float(parts[1])
                            }
                
                result.append(vehicle_dict)
            
            return jsonify({
                'vehicles': result,
                'count': len(result)
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/dashboard/stats', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """Get dashboard statistics - role-based filtering"""
    try:
        user_role = request.user.get('role')
        user_id = request.user.get('user_id')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get vehicle counts - filtered by role
            if user_role == 'admin':
                # Admin can see all vehicles
                cur.execute("SELECT COUNT(*) as total, status FROM vehicle GROUP BY status")
            else:
                # Owners can only see their own vehicles (must have owner_id set)
                cur.execute("""
                    SELECT COUNT(*) as total, status 
                    FROM vehicle 
                    WHERE owner_id = %s AND owner_id IS NOT NULL
                    GROUP BY status
                """, (user_id,))
            vehicles_by_status = {row['status']: row['total'] for row in cur.fetchall()}
            
            # Get alert counts - filtered by role
            if user_role == 'admin':
                # Admin can see all alerts
                cur.execute("""
                    SELECT COUNT(*) as total, status 
                    FROM alert 
                    WHERE status IN ('new', 'under_review')
                    GROUP BY status
                """)
            else:
                # Owners can only see alerts for their vehicles (must have owner_id set)
                cur.execute("""
                    SELECT COUNT(*) as total, a.status 
                    FROM alert a
                    INNER JOIN vehicle v ON a.vehicle_id = v.vehicle_id
                    WHERE v.owner_id = %s AND v.owner_id IS NOT NULL AND a.status IN ('new', 'under_review')
                    GROUP BY a.status
                """, (user_id,))
            alerts_by_status = {row['status']: row['total'] for row in cur.fetchall()}
            
            # Get alert counts by type - filtered by role
            if user_role == 'admin':
                cur.execute("""
                    SELECT COUNT(*) as total, alert_type 
                    FROM alert 
                    WHERE status IN ('new', 'under_review')
                    GROUP BY alert_type
                """)
            else:
                cur.execute("""
                    SELECT COUNT(*) as total, a.alert_type 
                    FROM alert a
                    INNER JOIN vehicle v ON a.vehicle_id = v.vehicle_id
                    WHERE v.owner_id = %s AND v.owner_id IS NOT NULL AND a.status IN ('new', 'under_review')
                    GROUP BY a.alert_type
                """, (user_id,))
            alerts_by_type = {row['alert_type']: row['total'] for row in cur.fetchall()}
            
            # Get alert counts by priority (severity-based) - filtered by role
            if user_role == 'admin':
                cur.execute("""
                    SELECT 
                        COUNT(*) FILTER (WHERE severity IN ('critical', 'high')) as high_priority,
                        COUNT(*) FILTER (WHERE severity = 'medium') as medium_priority,
                        COUNT(*) FILTER (WHERE severity = 'low') as low_priority
                    FROM alert 
                    WHERE status IN ('new', 'under_review')
                """)
            else:
                cur.execute("""
                    SELECT 
                        COUNT(*) FILTER (WHERE a.severity IN ('critical', 'high')) as high_priority,
                        COUNT(*) FILTER (WHERE a.severity = 'medium') as medium_priority,
                        COUNT(*) FILTER (WHERE a.severity = 'low') as low_priority
                    FROM alert a
                    INNER JOIN vehicle v ON a.vehicle_id = v.vehicle_id
                    WHERE v.owner_id = %s AND v.owner_id IS NOT NULL AND a.status IN ('new', 'under_review')
                """, (user_id,))
            priority_counts = cur.fetchone()
            
            # Get device counts - filtered by role
            # For now, return hardcoded values for demo (can be replaced with actual counts later)
            if user_role == 'admin':
                # Admin sees all devices
                device_count = 72  # Hardcoded for demo
                mic_count = 25
                camera_count = 18
            else:
                # Owners see devices for their vehicles (hardcoded for demo)
                device_count = 3  # Hardcoded: assume 3 devices per vehicle
                mic_count = 1
                camera_count = 1
            
            cur.close()
            
            return jsonify({
                'connectedCars': vehicles_by_status.get('active', 0),
                'onlineCars': vehicles_by_status.get('active', 0),
                'offlineCars': vehicles_by_status.get('inactive', 0),
                'activeAlerts': sum(alerts_by_status.values()),
                'emergencyAlerts': alerts_by_type.get('emergency', 0),
                'safetyAlerts': alerts_by_type.get('safety', 0),
                'anomalyAlerts': alerts_by_type.get('maintenance', 0),
                'highPriorityAlerts': priority_counts['high_priority'] if priority_counts else 0,
                'mediumPriorityAlerts': priority_counts['medium_priority'] if priority_counts else 0,
                'lowPriorityAlerts': priority_counts['low_priority'] if priority_counts else 0,
                'iotDevices': device_count,
                'microphones': mic_count,
                'cameras': camera_count
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/v1/test/process-audio', methods=['POST'])
@require_auth
def test_process_audio():
    """
    Test endpoint to process a local audio file
    Automatically links to the logged-in user
    Expected payload:
    {
        "filePath": "User1/1763163317.wav",
        "vehicleId": "User1" (optional, extracted from path if not provided)
    }
    """
    try:
        user_id = request.user.get('user_id')
        user_email = request.user.get('email')
        
        data = request.get_json()
        if not data or 'filePath' not in data:
            return jsonify({"error": "Missing required field: filePath"}), 400
        
        file_path = data['filePath']
        vehicle_id = data.get('vehicleId')
        
        # Extract vehicle ID from path if not provided
        if not vehicle_id:
            parts = file_path.split('/')
            for part in parts:
                if part and not any(part.endswith(ext) for ext in ['.wav', '.mp3', '.m4a', '.flac', '.ogg']):
                    vehicle_id = part
                    break
            if not vehicle_id:
                return jsonify({"error": "Could not extract vehicle ID from path"}), 400
        
        # Construct full local path
        local_file_path = os.path.join(LOCAL_STORAGE_PATH, file_path)
        
        if not os.path.exists(local_file_path):
            return jsonify({"error": f"File not found: {local_file_path}"}), 404
        
        # Ensure vehicle exists and is linked to current user
        # If user is admin, link to test user (testing@gmail.com) instead
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                
                # If admin is processing, link to test user instead
                owner_id_to_use = user_id
                if user_role == 'admin':
                    cur.execute("SELECT user_id FROM users WHERE email = 'testing@gmail.com'")
                    test_user_result = cur.fetchone()
                    if test_user_result:
                        owner_id_to_use = test_user_result[0]
                        print(f"Admin processing - linking vehicle to test user (testing@gmail.com)")
                
                # Check if vehicle exists
                cur.execute("SELECT vehicle_id, owner_id FROM vehicle WHERE vehicle_id = %s", (vehicle_id,))
                existing = cur.fetchone()
                
                if existing:
                    # Update owner if different
                    if existing[1] != owner_id_to_use:
                        cur.execute("UPDATE vehicle SET owner_id = %s WHERE vehicle_id = %s", (owner_id_to_use, vehicle_id))
                        conn.commit()
                        if user_role == 'admin':
                            print(f"Updated vehicle {vehicle_id} owner to test user")
                        else:
                            print(f"Updated vehicle {vehicle_id} owner to {user_email}")
                else:
                    # Create vehicle linked to owner
                    cur.execute("""
                        INSERT INTO vehicle (vehicle_id, owner_id, make, model, license_plate, status, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (vehicle_id, owner_id_to_use, 'Unknown', 'Unknown', vehicle_id, 'active'))
                    conn.commit()
                    if user_role == 'admin':
                        print(f"Created vehicle {vehicle_id} for test user")
                    else:
                        print(f"Created vehicle {vehicle_id} for user {user_email}")
                cur.close()
                conn.close()
        except Exception as e:
            print(f"Warning: Could not link vehicle to user: {e}")
        
        # Process the file
        try:
            from workers.ml_inference_worker import process_audio_file_local
            from services.alert_rule_engine import process_detection
            
            detection = process_audio_file_local(local_file_path, vehicle_id)
            
            if not detection:
                return jsonify({"error": "Failed to process audio file"}), 500
            
            # Process through alert engine
            alert = process_detection(detection)
            
            result = {
                "detection": {
                    "detectionId": detection['detectionId'],
                    "soundLabel": detection['soundLabel'],
                    "confidence": detection['confidence'],
                    "vehicleId": detection['carId']
                },
                "alert": None,
                "userId": str(user_id),
                "userEmail": user_email
            }
            
            if alert:
                result["alert"] = {
                    "alertId": alert['alertId'],
                    "alertType": alert['alertType'],
                    "severity": alert['severity'],
                    "priority": alert.get('priority', 'medium'),
                    "message": alert['message'],
                    "status": alert['status']
                }
            
            return jsonify(result), 200
            
        except ImportError as e:
            return jsonify({"error": f"Import error: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": f"Processing error: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/v1/process-audio-batch', methods=['POST'])
@require_auth
def process_audio_batch():
    """
    Process all audio files in a folder for the logged-in user
    Automatically links vehicles to the current user
    Expected payload:
    {
        "folderName": "User1" (optional, defaults to user's email prefix)
    }
    """
    try:
        user_id = request.user.get('user_id')
        user_email = request.user.get('email')
        user_role = request.user.get('role')
        
        data = request.get_json() or {}
        folder_name = data.get('folderName')
        
        # If folder name not provided, use email prefix or user_id
        if not folder_name:
            if user_email:
                folder_name = user_email.split('@')[0]  # Use email prefix
            else:
                folder_name = f"user_{user_id[:8]}"
        
        # Find audio files in the folder
        folder_path = os.path.join(LOCAL_STORAGE_PATH, folder_name)
        if not os.path.exists(folder_path):
            return jsonify({'error': f'Folder not found: {folder_name}'}), 404
        
        # Find all audio files
        audio_files = []
        for ext in ['.wav', '.mp3', '.m4a', '.flac', '.ogg']:
            audio_files.extend(Path(folder_path).glob(f'*{ext}'))
            audio_files.extend(Path(folder_path).glob(f'*{ext.upper()}'))
        
        if not audio_files:
            return jsonify({'error': f'No audio files found in {folder_name}'}), 404
        
        # Process files
        results = []
        try:
            from workers.ml_inference_worker import process_audio_file_local
            from services.alert_rule_engine import process_detection
            
            # Ensure vehicle exists and is linked to user
            # If admin is processing, link to test user instead
            owner_id_to_use = user_id
            if user_role == 'admin':
                conn_check = get_db_connection()
                if conn_check:
                    cur_check = conn_check.cursor()
                    cur_check.execute("SELECT user_id FROM users WHERE email = 'testing@gmail.com'")
                    test_user_result = cur_check.fetchone()
                    if test_user_result:
                        owner_id_to_use = test_user_result[0]
                    cur_check.close()
                    conn_check.close()
            
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO vehicle (vehicle_id, owner_id, make, model, license_plate, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (vehicle_id) DO UPDATE SET owner_id = %s
                """, (folder_name, owner_id_to_use, 'Unknown', 'Unknown', folder_name, 'active', owner_id_to_use))
                conn.commit()
                cur.close()
                conn.close()
            
            for file_path in audio_files:
                detection = process_audio_file_local(str(file_path), folder_name)
                if detection:
                    alert = process_detection(detection)
                    results.append({
                        'file': os.path.basename(str(file_path)),
                        'detection': detection['soundLabel'],
                        'confidence': detection['confidence'],
                        'alertCreated': alert is not None
                    })
        except ImportError as e:
            return jsonify({'error': f'Import error: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'Processing error: {str(e)}'}), 500
        
        return jsonify({
            'message': f'Processed {len(results)} files',
            'folder': folder_name,
            'userId': str(user_id),
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Validate required environment variables
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable is required")
        exit(1)
    
    # Create uploads directory if it doesn't exist
    os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)
    app.run(host='0.0.0.0', port=5001, debug=True)
