#!/usr/bin/env python3
"""
Test script to check what the model actually classifies for audio files
This helps debug classification issues
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.ml_inference_worker import process_audio_file_local, extract_features_with_yamnet, predict_sound_class

def test_audio_file(file_path):
    """Test a single audio file and show detailed classification results"""
    print(f"\n{'='*60}")
    print(f"Testing: {file_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return
    
    # Extract features
    print("\n1. Extracting features with YAMNet...")
    features = extract_features_with_yamnet(file_path)
    if not features:
        print("ERROR: Feature extraction failed")
        return
    print("✓ Features extracted")
    
    # Predict
    print("\n2. Classifying sound...")
    prediction = predict_sound_class(features)
    if not prediction:
        print("ERROR: Prediction failed")
        return
    
    # Show results
    print(f"\n{'='*60}")
    print("CLASSIFICATION RESULTS")
    print(f"{'='*60}")
    print(f"Primary Label: {prediction['primaryLabel']}")
    print(f"Confidence: {prediction['confidence']:.2%}")
    print(f"\nTop 3 Predictions:")
    for i, pred in enumerate(prediction['allPredictions'], 1):
        print(f"  {i}. {pred['label']}: {pred['confidence']:.2%}")
    print(f"{'='*60}\n")
    
    return prediction

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_model_classification.py <audio_file_path>")
        print("\nExample:")
        print("  python test_model_classification.py ../audio_uploads/User1/audio.wav")
        sys.exit(1)
    
    file_path = sys.argv[1]
    test_audio_file(file_path)

