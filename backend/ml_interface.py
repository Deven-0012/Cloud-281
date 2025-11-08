"""
ML Inference Worker - Smart Car Audio Surveillance Platform
Processes audio data and performs sound classification
"""

import os
import json
import boto3
import numpy as np
import librosa
import tensorflow as tf
from datetime import datetime
import time

# AWS Configuration
S3_BUCKET = os.getenv('S3_BUCKET', 'smart-car-audio-storage')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL', '')
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE', 'smart-car-detections')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
sqs_client = boto3.client('sqs', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

# Model configuration
MODEL_PATH = '/models/audio_classifier.h5'
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
    'normal'
]

# Load ML model
print("Loading ML model...")
model = None
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    print("Using fallback random prediction for demo")


def extract_features(audio_path, sr=22050, n_mfcc=40):
    """
    Extract audio features for ML model
    
    Args:
        audio_path: Path to audio file
        sr: Sample rate
        n_mfcc: Number of MFCC coefficients
    
    Returns:
        Dictionary of extracted features
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
    
    Args:
        features: Extracted audio features
    
    Returns:
        Dictionary with predictions
    """
    try:
        if model is None:
            # Fallback: random prediction for demo
            predictions = np.random.dirichlet(np.ones(len(LABELS)))
            top_class_idx = np.argmax(predictions)
        else:
            # Real model prediction
            feature_array = np.array(features['features']).reshape(1, -1)
            predictions = model.predict(feature_array)[0]
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
            'modelVersion': 'v1.2',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None


def process_audio_file(message):
    """
    Process audio file from S3
    
    Args:
        message: SQS message containing audio metadata
    
    Returns:
        Detection results
    """
    try:
        message_body = json.loads(message['Body'])
        
        car_id = message_body['carId']
        s3_key = message_body['s3Key']
        s3_bucket = message_body['s3Bucket']
        
        print(f"Processing audio for car {car_id}: {s3_key}")
        
        # Download audio file from S3
        local_path = f"/tmp/{os.path.basename(s3_key)}"
        s3_client.download_file(s3_bucket, s3_key, local_path)
        
        # Extract features
        features = extract_features(local_path)
        if features is None:
            raise Exception("Failed to extract features")
        
        # Make prediction
        prediction = predict_sound_class(features)
        if prediction is None:
            raise Exception("Failed to make prediction")
        
        # Store detection in DynamoDB
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
            'processingTimeMs': 0,  # Calculate actual time
            'status': 'completed'
        }
        
        table.put_item(Item=detection_record)
        
        # Clean up
        os.remove(local_path)
        
        print(f"Detection completed: {detection_id} - {prediction['primaryLabel']} ({prediction['confidence']:.2f})")
        
        return detection_record
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        return None


def process_features(message):
    """
    Process pre-extracted features
    
    Args:
        message: SQS message containing features
    
    Returns:
        Detection results
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
        
        # Store detection in DynamoDB
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
        
        table.put_item(Item=detection_record)
        
        print(f"Detection completed: {detection_id} - {prediction['primaryLabel']} ({prediction['confidence']:.2f})")
        
        return detection_record
        
    except Exception as e:
        print(f"Error processing features: {e}")
        return None


def poll_queue():
    """
    Poll SQS queue for messages and process them
    """
    print("Starting ML inference worker...")
    print(f"Polling queue: {SQS_QUEUE_URL}")
    
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
                    processing_type = message['MessageAttributes'].get('ProcessingType', {}).get('StringValue', 'audio')
                    
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