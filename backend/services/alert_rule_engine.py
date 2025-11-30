"""
Alert & Rule Engine - Smart Car Audio Surveillance Platform
Evaluates detections against rules and generates alerts
"""

import os
import json
import boto3
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from botocore.exceptions import ClientError, NoCredentialsError
import time

# Configuration
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', '')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
DATABASE_URL = os.getenv('DATABASE_URL')
# Don't raise error at import time - only check when actually connecting

# Initialize AWS clients with error handling
sns_client = None
if SNS_TOPIC_ARN:
    try:
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if aws_access_key and aws_secret_key:
            sns_client = boto3.client('sns', 
                                     region_name=AWS_REGION,
                                     aws_access_key_id=aws_access_key,
                                     aws_secret_access_key=aws_secret_key)
            print(f"SNS client initialized for topic: {SNS_TOPIC_ARN}")
        else:
            print("Warning: AWS credentials not found. SNS notifications will be disabled.")
    except (NoCredentialsError, ClientError) as e:
        print(f"Warning: Failed to initialize SNS client: {e}")
        sns_client = None

# Database connection helper with retry logic
def get_db_connection(max_retries=3):
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable is not set")
        print("Please set DATABASE_URL environment variable, e.g.:")
        print("  export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
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

# Rule definitions
RULES = {
    'engine_fault': {
        'threshold': 0.85,
        'severity': 'high',
        'alertType': 'mechanical',
        'notifyOwner': True,
        'notifyService': True,
        'message': 'Engine fault detected. Please check your vehicle immediately.'
    },
    'brake_issue': {
        'threshold': 0.80,
        'severity': 'critical',
        'alertType': 'safety',
        'notifyOwner': True,
        'notifyService': True,
        'message': 'Brake system issue detected. Stop vehicle safely and call for assistance.'
    },
    'tire_problem': {
        'threshold': 0.75,
        'severity': 'medium',
        'alertType': 'maintenance',
        'notifyOwner': True,
        'notifyService': False,
        'message': 'Tire issue or mechanical sound (drilling) detected. Schedule maintenance soon.'
    },
    'drilling': {
        'threshold': 0.75,
        'severity': 'medium',
        'alertType': 'maintenance',
        'notifyOwner': True,
        'notifyService': False,
        'message': 'Drilling or mechanical sound detected. Check vehicle for maintenance needs.'
    },
    'siren': {
        'threshold': 0.90,
        'severity': 'high',
        'alertType': 'emergency',
        'notifyOwner': True,
        'notifyService': False,
        'message': 'Emergency siren detected nearby.'
    },
    # Special handling: Very high confidence siren (>98%) might be gunshot
    # This is a workaround since the model doesn't have gunshot training
    'collision': {
        'threshold': 0.85,
        'severity': 'critical',
        'alertType': 'emergency',
        'notifyOwner': True,
        'notifyService': True,
        'message': 'Collision detected! Emergency services may be needed.'
    },
    'glass_break': {
        'threshold': 0.80,
        'severity': 'high',
        'alertType': 'security',
        'notifyOwner': True,
        'notifyService': True,
        'message': 'Glass break detected. Possible security breach.'
    },
    'distress_call': {
        'threshold': 0.85,
        'severity': 'critical',
        'alertType': 'emergency',
        'notifyOwner': True,
        'notifyService': True,
        'message': 'Distress call detected in vehicle. Immediate attention required.'
    },
    'gun_fire': {
        'threshold': 0.80,
        'severity': 'critical',
        'alertType': 'emergency',
        'notifyOwner': True,
        'notifyService': True,
        'message': 'Gun fire detected! Immediate emergency response required.'
    },
    'gunshot': {
        'threshold': 0.80,
        'severity': 'critical',
        'alertType': 'emergency',
        'notifyOwner': True,
        'notifyService': True,
        'message': 'Gunshot detected! Immediate emergency response required.'
    },
    'drilling': {
        'threshold': 0.75,
        'severity': 'medium',
        'alertType': 'maintenance',
        'notifyOwner': True,
        'notifyService': False,
        'message': 'Drilling or mechanical sound detected. Check vehicle for maintenance needs.'
    },
    'animal_sound': {
        'threshold': 0.70,
        'severity': 'low',
        'alertType': 'maintenance',
        'notifyOwner': True,
        'notifyService': False,
        'message': 'Animal sound (dog barking) detected in vehicle.'
    },
    'dog_barking': {
        'threshold': 0.70,
        'severity': 'low',
        'alertType': 'maintenance',
        'notifyOwner': True,
        'notifyService': False,
        'message': 'Dog barking detected in vehicle.'
    },
    'horn': {
        'threshold': 0.80,
        'severity': 'medium',
        'alertType': 'safety',
        'notifyOwner': True,
        'notifyService': False,
        'message': 'Horn sound detected. Check for traffic or safety concerns.'
    }
}


def should_generate_alert(detection):
    """
    Evaluate if detection meets criteria for alert generation
    
    Args:
        detection: Detection record from ML inference
    
    Returns:
        Tuple (should_alert, rule)
    """
    sound_label = detection['soundLabel']
    confidence = float(detection['confidence'])
    
    # Special case: Very high confidence siren (>98%) might actually be gunshot
    # The model misclassifies gunshots as sirens, so we treat very high confidence sirens as potential gunshots
    if sound_label == 'siren' and confidence > 0.98:
        print(f"Very high confidence siren ({confidence:.2%}) - treating as potential gunshot")
        if 'gun_fire' in RULES:
            rule = RULES['gun_fire'].copy()
            rule['message'] = 'Gunshot detected (classified as siren by model)! Immediate emergency response required.'
            # Store original label and override for gunshot detection
            detection['originalSoundLabel'] = sound_label
            detection['soundLabel'] = 'gun_fire'  # Change label so duplicate check uses gun_fire
            return True, rule
    
    # Special case: Horn classified as siren - check if it's actually a horn
    # If siren confidence is moderate (90-98%), it might be a horn misclassified
    if sound_label == 'siren' and 0.90 <= confidence <= 0.98:
        # Check top predictions to see if horn is in top 3
        all_predictions = detection.get('allPredictions', [])
        for pred in all_predictions:
            if pred['label'] == 'horn' and pred['confidence'] > 0.10:
                print(f"Siren ({confidence:.2%}) might be horn - checking horn rule")
                if 'horn' in RULES:
                    # Use horn rule if confidence meets threshold
                    detection['originalSoundLabel'] = sound_label
                    detection['soundLabel'] = 'horn'
                    rule = RULES['horn']
                    # Use the horn confidence from predictions
                    horn_confidence = pred['confidence']
                    if horn_confidence >= rule['threshold']:
                        detection['confidence'] = horn_confidence
                        return True, rule
    
    # Special case: Horn classified as horn but might be dog barking
    # If horn confidence is moderate and animal_sound is in top predictions
    if sound_label == 'horn' and confidence < 0.90:
        all_predictions = detection.get('allPredictions', [])
        for pred in all_predictions:
            if pred['label'] == 'animal_sound' and pred['confidence'] > 0.15:
                print(f"Horn ({confidence:.2%}) might be dog barking - checking animal_sound rule")
                if 'animal_sound' in RULES:
                    detection['originalSoundLabel'] = sound_label
                    detection['soundLabel'] = 'animal_sound'
                    rule = RULES['animal_sound']
                    animal_confidence = pred['confidence']
                    if animal_confidence >= rule['threshold']:
                        detection['confidence'] = animal_confidence
                        return True, rule
    
    # Special case: Tire problem with very high confidence might be drilling
    # Drilling sounds can be misclassified as tire_problem
    if sound_label == 'tire_problem' and confidence > 0.95:
        print(f"Very high confidence tire_problem ({confidence:.2%}) - treating as potential drilling")
        # Store original and map to drilling
        detection['originalSoundLabel'] = sound_label
        detection['soundLabel'] = 'drilling'
        if 'drilling' in RULES:
            rule = RULES['drilling']
            if confidence >= rule['threshold']:
                return True, rule
        # Fall back to tire_problem rule
        if 'tire_problem' in RULES:
            rule = RULES['tire_problem']
            if confidence >= rule['threshold']:
                return True, rule
    
    # Check if sound label has a rule
    if sound_label not in RULES:
        # Check if it's a gun-related sound that might have been misclassified
        # If model outputs collision/glass_break with very high confidence, it might be gunshot
        gun_related_labels = ['collision', 'glass_break']
        if sound_label in gun_related_labels and confidence > 0.90:
            print(f"High confidence {sound_label} ({confidence:.2%}) - checking if it might be gunshot")
            # Use gun_fire rule for very high confidence collision/glass_break
            if 'gun_fire' in RULES:
                rule = RULES['gun_fire']
                if confidence >= rule['threshold']:
                    print(f"Treating {sound_label} as potential gunshot (confidence: {confidence:.2%})")
                    return True, rule
        
        print(f"No rule found for sound label: {sound_label} (confidence: {confidence:.2%})")
        return False, None
    
    rule = RULES[sound_label]
    
    # Check if confidence meets threshold
    if confidence >= rule['threshold']:
        return True, rule
    
    print(f"Confidence {confidence:.2%} below threshold {rule['threshold']:.2%} for {sound_label}")
    return False, None


def check_duplicate_alert(car_id, sound_label, time_window_minutes=0.5):
    """
    Check if similar alert was recently generated
    
    Args:
        car_id: Vehicle ID
        sound_label: Sound classification label
        time_window_minutes: Time window for duplicate check (reduced to 2 minutes)
    
    Returns:
        Boolean indicating if duplicate exists
    """
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        cur = conn.cursor()
        # Check for exact same sound_label within time window
        # But allow different sound labels even if from same vehicle
        cur.execute("""
            SELECT alert_id FROM alert 
            WHERE vehicle_id = %s 
            AND sound_label = %s 
            AND created_at > %s
            LIMIT 1
        """, (car_id, sound_label, cutoff_time))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            print(f"Duplicate alert found: {sound_label} for {car_id} within last {time_window_minutes} minutes")
        
        return result is not None
        
    except Exception as e:
        print(f"Error checking duplicates: {e}")
        return False


def create_alert(detection, rule):
    """
    Create alert record from detection
    
    Args:
        detection: Detection record
        rule: Matching rule configuration
    
    Returns:
        Alert record
    """
    alert_id = f"ALERT-{detection['carId']}-{int(datetime.utcnow().timestamp() * 1000)}"
    
    # Generate random location for demo (in production, get from vehicle GPS)
    import random
    # San Francisco area coordinates
    lat = 37.7749 + random.uniform(-0.1, 0.1)
    lng = -122.4194 + random.uniform(-0.1, 0.1)
    
    # Map severity to priority (high/medium/low)
    severity = rule['severity']
    if severity == 'critical':
        priority = 'high'
    elif severity == 'high':
        priority = 'high'
    elif severity == 'medium':
        priority = 'medium'
    else:
        priority = 'low'
    
    alert = {
        'alertId': alert_id,
        'carId': detection['carId'],
        'detectionId': detection['detectionId'],
        'timestamp': datetime.utcnow().isoformat(),
        'soundLabel': detection['soundLabel'],
        'confidence': float(detection['confidence']),
        'severity': rule['severity'],
        'priority': priority,  # Add priority field
        'alertType': rule['alertType'],
        'message': rule['message'],
        'status': 'new',
        'notifiedOwner': False,
        'notifiedService': False,
        'acknowledgedAt': None,
        'resolvedAt': None,
        'location': (lat, lng),  # POINT type for PostgreSQL
        'metadata': {
            'modelVersion': detection.get('modelVersion', 'unknown'),
            's3Key': detection.get('s3Key', ''),
            'allPredictions': detection.get('allPredictions', [])
        }
    }
    
    return alert


def send_notification(alert, notification_type='owner'):
    """
    Send notification via SNS
    
    Args:
        alert: Alert record
        notification_type: 'owner' or 'service'
    
    Returns:
        Boolean indicating success
    """
    try:
        if not sns_client or not SNS_TOPIC_ARN:
            print("SNS not configured, skipping notification")
            return False
        
        subject = f"[{alert['severity'].upper()}] Smart Car Alert: {alert['soundLabel']}"
        
        message = f"""
Smart Car Audio Surveillance Alert

Alert ID: {alert['alertId']}
Vehicle: {alert['carId']}
Time: {alert['timestamp']}
Type: {alert['alertType']}
Severity: {alert['severity']}
Detection: {alert['soundLabel']} (Confidence: {float(alert['confidence']):.2%})

Message:
{alert['message']}

Please log in to the dashboard for more details and to acknowledge this alert.
"""
        
        # Send SNS notification
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message,
            MessageAttributes={
                'AlertType': {'DataType': 'String', 'StringValue': alert['alertType']},
                'Severity': {'DataType': 'String', 'StringValue': alert['severity']},
                'CarId': {'DataType': 'String', 'StringValue': alert['carId']}
            }
        )
        
        print(f"Notification sent: {response['MessageId']}")
        return True
        
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False


def process_detection(detection):
    """
    Process detection and generate alert if needed
    
    Args:
        detection: Detection record from ML inference
    
    Returns:
        Alert record if generated, None otherwise
    """
    try:
        print(f"Evaluating detection: {detection['detectionId']}")
        
        # Check if alert should be generated
        should_alert, rule = should_generate_alert(detection)
        
        if not should_alert:
            print(f"No alert needed for {detection['soundLabel']} (confidence: {detection['confidence']})")
            return None
        
        # Check for duplicate alerts - use the actual sound label (might have been changed for gunshot)
        # Use a unique identifier that includes detection ID to avoid false duplicates
        actual_sound_label = detection.get('soundLabel', detection.get('originalSoundLabel', ''))
        # Only check for duplicates if it's the exact same sound within a very short window (30 seconds)
        # This allows different files to create alerts even if processed quickly
        if check_duplicate_alert(detection['carId'], actual_sound_label, time_window_minutes=0.5):
            print(f"Duplicate alert suppressed for {detection['carId']} - {actual_sound_label} (within 30 seconds)")
            return None
        
        # Create alert
        alert = create_alert(detection, rule)
        
        # Store alert in PostgreSQL
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to database")
            return None
        
        try:
            cur = conn.cursor()
            # Insert alert with location (priority is derived from severity in API response)
            cur.execute("""
                INSERT INTO alert 
                (alert_id, vehicle_id, detection_id, alert_type, severity, sound_label, 
                 confidence, message, status, notified_owner, notified_service, location, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, POINT(%s, %s), %s)
            """, (
                alert['alertId'],
                alert['carId'],
                alert['detectionId'],
                alert['alertType'],
                alert['severity'],
                alert['soundLabel'],
                alert['confidence'],
                alert['message'],
                alert['status'],
                alert['notifiedOwner'],
                alert['notifiedService'],
                alert['location'][0],  # lat
                alert['location'][1],  # lng
                json.dumps(alert['metadata'])
            ))
            conn.commit()
            cur.close()
            print(f"Alert created: {alert['alertId']}")
            
            # Send notifications
            if rule['notifyOwner']:
                if send_notification(alert, 'owner'):
                    alert['notifiedOwner'] = True
            
            if rule['notifyService']:
                if send_notification(alert, 'service'):
                    alert['notifiedService'] = True
            
            # Update alert with notification status
            if alert['notifiedOwner'] or alert['notifiedService']:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE alert 
                    SET notified_owner = %s, notified_service = %s
                    WHERE alert_id = %s
                """, (alert['notifiedOwner'], alert['notifiedService'], alert['alertId']))
                conn.commit()
                cur.close()
            
            return alert
            
        except Exception as e:
            conn.rollback()
            print(f"Error storing alert: {e}")
            return None
        finally:
            conn.close()
        
    except Exception as e:
        print(f"Error processing detection: {e}")
        return None


def scan_and_process_detections():
    """
    Scan PostgreSQL for new detections and process them
    This would typically be triggered by database triggers or streams in production
    """
    try:
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to database")
            return
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT d.*, 
                   CASE WHEN a.alert_id IS NOT NULL THEN true ELSE false END as has_alert
            FROM detection d
            LEFT JOIN alert a ON d.detection_id = a.detection_id
            WHERE d.created_at > %s 
            AND d.status = 'completed'
            AND a.alert_id IS NULL
            ORDER BY d.created_at DESC
        """, (cutoff_time,))
        
        detections = cur.fetchall()
        cur.close()
        conn.close()
        
        print(f"Found {len(detections)} detections to process")
        
        for detection in detections:
            detection_dict = dict(detection)
            detection_dict['carId'] = detection_dict['vehicle_id']
            detection_dict['detectionId'] = detection_dict['detection_id']
            detection_dict['soundLabel'] = detection_dict['sound_label']
            detection_dict['confidence'] = float(detection_dict['confidence'])
            detection_dict['timestamp'] = detection_dict['created_at'].isoformat()
            process_detection(detection_dict)
        
    except Exception as e:
        print(f"Error scanning detections: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import time
    
    print("Starting Alert & Rule Engine...")
    
    while True:
        try:
            scan_and_process_detections()
            time.sleep(10)  # Check every 10 seconds
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(10)