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

# Configuration
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', '')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Initialize AWS clients
sns_client = boto3.client('sns', region_name=AWS_REGION) if SNS_TOPIC_ARN else None

# Database connection helper
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
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
        'message': 'Tire issue detected. Schedule maintenance soon.'
    },
    'siren': {
        'threshold': 0.90,
        'severity': 'high',
        'alertType': 'emergency',
        'notifyOwner': True,
        'notifyService': False,
        'message': 'Emergency siren detected nearby.'
    },
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
    
    # Check if sound label has a rule
    if sound_label not in RULES:
        return False, None
    
    rule = RULES[sound_label]
    
    # Check if confidence meets threshold
    if confidence >= rule['threshold']:
        return True, rule
    
    return False, None


def check_duplicate_alert(car_id, sound_label, time_window_minutes=5):
    """
    Check if similar alert was recently generated
    
    Args:
        car_id: Vehicle ID
        sound_label: Sound classification label
        time_window_minutes: Time window for duplicate check
    
    Returns:
        Boolean indicating if duplicate exists
    """
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        cur = conn.cursor()
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
    
    alert = {
        'alertId': alert_id,
        'carId': detection['carId'],
        'detectionId': detection['detectionId'],
        'timestamp': datetime.utcnow().isoformat(),
        'soundLabel': detection['soundLabel'],
        'confidence': float(detection['confidence']),
        'severity': rule['severity'],
        'alertType': rule['alertType'],
        'message': rule['message'],
        'status': 'new',
        'notifiedOwner': False,
        'notifiedService': False,
        'acknowledgedAt': None,
        'resolvedAt': None,
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
        
        # Check for duplicate alerts
        if check_duplicate_alert(detection['carId'], detection['soundLabel']):
            print(f"Duplicate alert suppressed for {detection['carId']}")
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
            cur.execute("""
                INSERT INTO alert 
                (alert_id, vehicle_id, detection_id, alert_type, severity, sound_label, 
                 confidence, message, status, notified_owner, notified_service, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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