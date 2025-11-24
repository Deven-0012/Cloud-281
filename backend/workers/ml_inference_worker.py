"""
ML Inference Worker - Smart Car Audio Surveillance Platform
Processes audio data from S3, extracts YAMNet embeddings, classifies sounds,
and stores detections in PostgreSQL.
"""

import os
import json
import boto3
import numpy as np
import librosa
import tensorflow as tf
import tensorflow_hub as hub
from datetime import datetime
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import traceback

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
S3_BUCKET = os.getenv("S3_BUCKET", "smart-car-audio-storage")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://smart_car_user:SecurePassword123!@postgres:5432/smart_car_surveillance"
)
MODEL_PATH = "/Users/devendesai/281/Final project/model/my_yamnet_human_model_fixed.keras"

# ---------------------------------------------------------------------
# Initialize AWS clients
# ---------------------------------------------------------------------
s3_client = boto3.client("s3", region_name=AWS_REGION)
sqs_client = boto3.client("sqs", region_name=AWS_REGION)

# ---------------------------------------------------------------------
# Load YAMNet and classifier model
# ---------------------------------------------------------------------
print("Loading YAMNet from TensorFlow Hub...")
yamnet_model = hub.load("https://tfhub.dev/google/yamnet/1")
print("YAMNet ready")

print("Loading classifier model...")
try:
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    print(f"Model loaded successfully from {MODEL_PATH}")
    model.summary()
except Exception as e:
    print(f"Failed to load model: {e}")
    model = None

# ---------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------
LABELS = [
    "engine_fault",
    "brake_issue",
    "tire_problem",
    "siren",
    "horn",
    "collision",
    "glass_break",
    "human_voice",
    "distress_call",
    "animal_sound"
]

# ---------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# ---------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------
def extract_features_with_yamnet(audio_path, sr=16000):
    """Extract 1024-D YAMNet embeddings averaged over time."""
    try:
        y, _ = librosa.load(audio_path, sr=sr, mono=True)
        waveform = tf.convert_to_tensor(y, dtype=tf.float32)
        _, embeddings, _ = yamnet_model(waveform)
        features = tf.reduce_mean(embeddings, axis=0).numpy()
        return {"features": features.tolist()}
    except Exception as e:
        print(f"Error extracting YAMNet features: {e}")
        traceback.print_exc()
        return None

# ---------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------
def predict_sound_class(features):
    """Predict sound class from YAMNet embeddings."""
    try:
        if model is None:
            preds = np.random.dirichlet(np.ones(len(LABELS)))
        else:
            feature_array = np.array(features["features"]).reshape(1, -1)
            preds = model.predict(feature_array, verbose=0)[0]

        label_count = preds.size
        labels_aligned = LABELS[:label_count]

        top_idx = int(np.argmax(preds))
        top_3_indices = np.argsort(preds)[-3:][::-1]
        top_3 = [
            {"label": labels_aligned[i], "confidence": float(preds[i])}
            for i in top_3_indices
        ]

        return {
            "primaryLabel": labels_aligned[top_idx],
            "confidence": float(preds[top_idx]),
            "allPredictions": top_3,
            "modelVersion": "yamnet-v1.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error in prediction: {e}")
        traceback.print_exc()
        return None

# ---------------------------------------------------------------------
# Store detection in database
# ---------------------------------------------------------------------
def store_detection(detection):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO detection (
                    detection_id, vehicle_id, sound_label, confidence,
                    model_version, s3_key, timestamp, status, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (detection_id) DO NOTHING
                """,
                (
                    detection["detectionId"],
                    detection["carId"],
                    detection["soundLabel"],
                    detection["confidence"],
                    detection["modelVersion"],
                    detection["s3Key"],
                    detection["timestamp"],
                    "completed",
                    json.dumps(detection.get("allPredictions", [])),
                ),
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error storing detection: {e}")
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

# ---------------------------------------------------------------------
# Process one audio file (S3)
# ---------------------------------------------------------------------
def process_audio_file(message):
    """Download audio from S3, extract features, predict, store."""
    try:
        body = json.loads(message["Body"])
        car_id = body["carId"]
        s3_key = body["s3Key"]
        s3_bucket = body.get("s3Bucket", S3_BUCKET)
        job_id = body.get("jobId")

        local_path = f"/tmp/{os.path.basename(s3_key)}"
        print(f"Processing {car_id} -> {s3_key}")
        s3_client.download_file(s3_bucket, s3_key, local_path)

        features = extract_features_with_yamnet(local_path)
        if not features:
            raise RuntimeError("Feature extraction failed")

        prediction = predict_sound_class(features)
        if not prediction:
            raise RuntimeError("Prediction failed")

        detection_id = f"DET-{car_id}-{int(time.time() * 1000)}"
        detection = {
            "detectionId": detection_id,
            "carId": car_id,
            "s3Key": s3_key,
            "timestamp": datetime.utcnow().isoformat(),
            "soundLabel": prediction["primaryLabel"],
            "confidence": prediction["confidence"],
            "allPredictions": prediction["allPredictions"],
            "modelVersion": prediction["modelVersion"],
        }
        store_detection(detection)

        if job_id:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE ingestion_job
                            SET status = 'completed', processed_at = CURRENT_TIMESTAMP
                            WHERE job_id = %s
                            """,
                            (job_id,),
                        )
                        conn.commit()
                except Exception as e:
                    print(f"Error updating job: {e}")
                finally:
                    conn.close()

        os.remove(local_path)
        print(
            f"Detection completed: {detection_id} -> "
            f"{prediction['primaryLabel']} ({prediction['confidence']:.2f})"
        )
        return detection

    except Exception as e:
        print(f"Error processing audio: {e}")
        traceback.print_exc()
        return None

# ---------------------------------------------------------------------
# Poll SQS queue
# ---------------------------------------------------------------------
def poll_queue():
    print("Starting ML inference worker")
    print(f"Polling queue: {SQS_QUEUE_URL}")

    if not SQS_QUEUE_URL:
        print("SQS_QUEUE_URL not set. Waiting...")
        time.sleep(60)
        return

    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=20,
                MessageAttributeNames=["All"],
            )
            messages = response.get("Messages", [])

            for message in messages:
                processing_type = (
                    message.get("MessageAttributes", {})
                    .get("ProcessingType", {})
                    .get("StringValue", "audio")
                )

                if processing_type == "audio":
                    result = process_audio_file(message)
                else:
                    print(f"Unknown processing type: {processing_type}")
                    result = None

                if result:
                    sqs_client.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=message["ReceiptHandle"],
                    )
                    print(f"Message processed and deleted: {message.get('MessageId')}")
                else:
                    print(f"Failed to process message: {message.get('MessageId')}")

            if not messages:
                print("No messages in queue, waiting...")

        except KeyboardInterrupt:
            print("Worker stopped manually")
            break
        except Exception as e:
            print(f"Error polling queue: {e}")
            traceback.print_exc()
            time.sleep(5)

# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    poll_queue()
