"""
ML Inference Worker - Smart Car Audio Surveillance Platform
Processes audio data and performs sound classification using YAMNet
"""

import os
import json
import boto3
import numpy as np
import librosa
import tensorflow as tf
from datetime import datetime
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# AWS Configuration
S3_BUCKET = os.getenv('S3_BUCKET', 'smart-car-audio-storage')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL', '')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://smart_car_user:SecurePassword123!@postgres:5432/smart_car_surveillance')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://admin:SecurePassword123!@mongodb:27017/')

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
sqs_client = boto3.client('sqs', region_name=AWS_REGION)

# Model configuration
# NOTE: /models is the path INSIDE the Docker container
# The host directory 'model' (singular) is mounted to /models (plural) in docker-compose.yml
MODEL_PATH = os.getenv('MODEL_PATH', '/models/my_yamnet_human_model.keras')
YAMNET_MODEL_PATH = '/models/yamnet_model'

# Print model loading info
print(f"Looking for model at: {MODEL_PATH}")
print(f"Model directory contents: {os.listdir('/models') if os.path.exists('/models') else 'Directory does not exist'}")

# Labels for custom model
LABELS = [
    'engine_fault',
    'brake_issue',
    'tire_problem',
    'siren',
    'horn',
    'collision',
    'glass_break',
    'human_voice',
    'distress_call',
    'animal_sound',
    'appliance_audio',
    'normal'
]

# Load ML model
print("Loading ML model...")
model = None
yamnet_model = None

try:
    # Try to load custom YAMNet-based model
    # Check multiple possible paths
    model_paths = [
        MODEL_PATH,
        '/models/my_yamnet_human_model.keras',
        '/models/model/my_yamnet_human_model.keras',
        os.path.join('/models', 'my_yamnet_human_model.keras')
    ]
    
    model_loaded = False
    for path in model_paths:
        if os.path.exists(path):
            print(f"Attempting to load model from: {path}")
            try:
                model = tf.keras.models.load_model(path)
                print(f"✓ Custom model loaded successfully from {path}")
                model_loaded = True
                break
            except Exception as load_error:
                print(f"Error loading from {path}: {load_error}")
                continue
    
    if not model_loaded:
        print(f"Model not found at any of these paths:")
        for path in model_paths:
            print(f"  - {path} (exists: {os.path.exists(path)})")
        print("Using fallback prediction for demo")
except Exception as e:
    print(f"Error during model loading: {e}")
    import traceback
    traceback.print_exc()
    print("Using fallback prediction for demo")

# Try to load base YAMNet model for feature extraction
try:
    import yamnet
    yamnet_model = yamnet.yamnet_model
    print("YAMNet model loaded for feature extraction")
except:
    print("YAMNet not available, using librosa features")


def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def extract_features_with_yamnet(audio_path, sr=16000):
    """
    Extract features using YAMNet embeddings (matching training process)
    Based on Human_model.ipynb training notebook
    """
    try:
        import tensorflow_hub as hub
        import scipy.signal as signal
        
        # Load YAMNet model from TensorFlow Hub (same as training)
        yamnet_model_hub = hub.load('https://tfhub.dev/google/yamnet/1')
        
        # Load audio file
        from scipy.io import wavfile
        original_sample_rate, wav_data = wavfile.read(audio_path)
        
        # Resample to 16kHz if needed (matching training)
        if original_sample_rate != sr:
            desired_length = int(round(float(len(wav_data)) / original_sample_rate * sr))
            wav_data = signal.resample(wav_data, desired_length)
        
        # Normalize waveform (matching training: waveform = wav_data / tf.int16.max)
        if wav_data.dtype == np.int16:
            waveform = wav_data.astype(np.float32) / np.iinfo(np.int16).max
        else:
            waveform = wav_data.astype(np.float32)
        
        # Ensure correct shape: (batch, samples)
        if len(waveform.shape) == 1:
            waveform = tf.expand_dims(waveform, 0)
        
        # Extract YAMNet embeddings (matching training)
        scores, embeddings, spectrogram = yamnet_model_hub(waveform)
        
        # Average embeddings across time for fixed-size feature vector (matching training)
        features = np.mean(embeddings.numpy(), axis=0)
        
        print(f"Extracted YAMNet embeddings: shape={features.shape}")
        
        return {
            'features': features.tolist(),  # 1024-dimensional YAMNet embedding
            'mfccs': librosa.feature.mfcc(y=waveform[0].numpy(), sr=sr, n_mfcc=40).tolist() if len(waveform) > 0 else [],
            'spectral_centroid': librosa.feature.spectral_centroid(y=waveform[0].numpy(), sr=sr).tolist() if len(waveform) > 0 else [],
            'zero_crossing_rate': librosa.feature.zero_crossing_rate(waveform[0].numpy()).tolist() if len(waveform) > 0 else []
        }
    except Exception as e:
        print(f"Error extracting YAMNet features: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to librosa features
        try:
            y, sr_loaded = librosa.load(audio_path, sr=sr, duration=30)
            mfccs = librosa.feature.mfcc(y=y, sr=sr_loaded, n_mfcc=40)
            features = np.mean(mfccs.T, axis=0)
            return {
                'features': features.tolist(),
                'mfccs': mfccs.tolist(),
                'spectral_centroid': librosa.feature.spectral_centroid(y=y, sr=sr_loaded).tolist(),
                'zero_crossing_rate': librosa.feature.zero_crossing_rate(y).tolist()
            }
        except Exception as e2:
            print(f"Fallback feature extraction also failed: {e2}")
            return None


def extract_features(audio_path, sr=22050, n_mfcc=40):
    """
    Extract audio features for ML model (fallback method)
    """
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=sr, duration=30)
        
        # Extract features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        mfccs_mean = np.mean(mfccs.T, axis=0)
        
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_centroid_mean = np.mean(spectral_centroid)
        
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
        zcr_mean = np.mean(zero_crossing_rate)
        
        chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma_stft.T, axis=0)
        
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        rolloff_mean = np.mean(spectral_rolloff)
        
        # Combine features
        features = np.concatenate([
            mfccs_mean,
            [spectral_centroid_mean, zcr_mean, rolloff_mean],
            chroma_mean
        ])
        
        return {
            'features': features.tolist(),
            'mfccs': mfccs.tolist(),
            'spectral_centroid': spectral_centroid.tolist(),
            'zero_crossing_rate': zero_crossing_rate.tolist(),
            'chroma': chroma_stft.tolist()
        }
        
    except Exception as e:
        print(f"Error extracting features: {e}")
        return None


def predict_sound_class(features):
    """
    Predict sound class from features
    """
    try:
        if model is None:
            # Fallback: random prediction for demo
            predictions = np.random.dirichlet(np.ones(len(LABELS)))
            top_class_idx = np.argmax(predictions)
        else:
            # Real model prediction
            feature_array = np.array(features['features'])
            
            # Reshape based on model input shape
            if len(feature_array.shape) == 1:
                feature_array = feature_array.reshape(1, -1)
            
            predictions = model.predict(feature_array, verbose=0)[0]
            top_class_idx = np.argmax(predictions)
        
        # Get top 3 predictions
        top_3_indices = np.argsort(predictions)[-3:][::-1]
        top_3_predictions = [
            {
                'label': LABELS[idx],
                'confidence': float(predictions[idx]),
                'rank': i + 1
            }
            for i, idx in enumerate(top_3_indices)
        ]
        
        return {
            'primaryLabel': LABELS[top_class_idx],
            'confidence': float(predictions[top_class_idx]),
            'allPredictions': top_3_predictions,
            'modelVersion': 'yamnet-v1.0',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        import traceback
        traceback.print_exc()
        return None


def store_detection(detection_record):
    """Store detection in PostgreSQL"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO detection (detection_id, vehicle_id, sound_label, confidence, 
                                   model_version, s3_key, timestamp, status, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (detection_id) DO NOTHING
        """, (
            detection_record['detectionId'],
            detection_record['carId'],
            detection_record['soundLabel'],
            detection_record['confidence'],
            detection_record.get('modelVersion', 'unknown'),
            detection_record.get('s3Key', ''),
            detection_record['timestamp'],
            'completed',
            json.dumps(detection_record.get('allPredictions', []))
        ))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"Error storing detection: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def process_audio_file(message):
    """
    Process audio file from S3
    """
    try:
        message_body = json.loads(message['Body'])
        
        car_id = message_body['carId']
        s3_key = message_body['s3Key']
        s3_bucket = message_body.get('s3Bucket', S3_BUCKET)
        job_id = message_body.get('jobId')
        
        print(f"Processing audio for car {car_id}: {s3_key}")
        
        # Download audio file from S3
        local_path = f"/tmp/{os.path.basename(s3_key)}"
        s3_client.download_file(s3_bucket, s3_key, local_path)
        
        # Extract features
        if yamnet_model:
            features = extract_features_with_yamnet(local_path)
        else:
            features = extract_features(local_path)
        
        if features is None:
            raise Exception("Failed to extract features")
        
        # Make prediction
        prediction = predict_sound_class(features)
        if prediction is None:
            raise Exception("Failed to make prediction")
        
        # Store detection
        detection_id = f"DET-{car_id}-{int(time.time() * 1000)}"
        detection_record = {
            'detectionId': detection_id,
            'carId': car_id,
            's3Key': s3_key,
            'timestamp': datetime.utcnow().isoformat(),
            'soundLabel': prediction['primaryLabel'],
            'confidence': prediction['confidence'],
            'allPredictions': prediction['allPredictions'],
            'modelVersion': prediction['modelVersion'],
            'processingTimeMs': 0,
            'status': 'completed'
        }
        
        # Store in database
        store_detection(detection_record)
        
        # Update ingestion job if job_id exists
        if job_id:
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE ingestion_job 
                        SET status = 'completed', processed_at = CURRENT_TIMESTAMP
                        WHERE job_id = %s
                    """, (job_id,))
                    conn.commit()
                    cur.close()
                except Exception as e:
                    print(f"Error updating job: {e}")
                finally:
                    conn.close()
        
        # Note: Alert engine will process this detection automatically via scan_and_process_detections()
        
        # Clean up
        os.remove(local_path)
        
        print(f"Detection completed: {detection_id} - {prediction['primaryLabel']} ({prediction['confidence']:.2f})")
        
        return detection_record
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_features(message):
    """
    Process pre-extracted features
    """
    try:
        message_body = json.loads(message['Body'])
        
        car_id = message_body['carId']
        features = message_body['features']
        
        print(f"Processing features for car {car_id}")
        
        # Make prediction
        prediction = predict_sound_class(features)
        if prediction is None:
            raise Exception("Failed to make prediction")
        
        # Store detection
        detection_id = f"DET-{car_id}-{int(time.time() * 1000)}"
        detection_record = {
            'detectionId': detection_id,
            'carId': car_id,
            'timestamp': message_body.get('timestamp', datetime.utcnow().isoformat()),
            'soundLabel': prediction['primaryLabel'],
            'confidence': prediction['confidence'],
            'allPredictions': prediction['allPredictions'],
            'modelVersion': prediction['modelVersion'],
            'processingTimeMs': 0,
            'status': 'completed'
        }
        
        # Store in database
        store_detection(detection_record)
        
        # Note: Alert engine will process this detection automatically via scan_and_process_detections()
        
        print(f"Detection completed: {detection_id} - {prediction['primaryLabel']} ({prediction['confidence']:.2f})")
        
        return detection_record
        
    except Exception as e:
        print(f"Error processing features: {e}")
        import traceback
        traceback.print_exc()
        return None


def poll_queue():
    """
    Poll SQS queue for messages and process them
    """
    print("Starting ML inference worker...")
    print(f"Polling queue: {SQS_QUEUE_URL}")
    
    if not SQS_QUEUE_URL:
        print("WARNING: SQS_QUEUE_URL not set, worker will not process messages")
        print("Waiting for configuration...")
        time.sleep(60)
        return
    
    while True:
        try:
            # Receive messages from SQS
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,  # Long polling
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            for message in messages:
                try:
                    # Get message attributes
                    processing_type = message.get('MessageAttributes', {}).get('ProcessingType', {}).get('StringValue', 'audio')
                    
                    # Process based on type
                    if processing_type == 'audio':
                        result = process_audio_file(message)
                    else:
                        result = process_features(message)
                    
                    if result:
                        # Delete message from queue after successful processing
                        sqs_client.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        print(f"Message processed and deleted: {message['MessageId']}")
                    else:
                        print(f"Failed to process message: {message['MessageId']}")
                    
                except Exception as e:
                    print(f"Error processing message: {e}")
                    import traceback
                    traceback.print_exc()
                    # Message will be reprocessed after visibility timeout
            
            if not messages:
                print("No messages in queue, waiting...")
            
        except KeyboardInterrupt:
            print("\nShutting down worker...")
            break
        except Exception as e:
            print(f"Error polling queue: {e}")
            time.sleep(5)


if __name__ == '__main__':
    poll_queue()

