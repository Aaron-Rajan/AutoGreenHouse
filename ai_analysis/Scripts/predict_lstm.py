# Adaptive Model

import numpy as np
from tensorflow.keras.models import load_model
from data_preprocessing import load_and_preprocess_data

# Load trained models
prediction_model = load_model("../models/adaptive_threshold_model.keras")
threshold_model = load_model("../models/adaptive_threshold_model.keras")

# Load test data
file_path = "../Data/greenhouse_sensor_data.csv"
_, X_test, _, y_test, scaler = load_and_preprocess_data(file_path)

# Get AI-Generated Thresholds for test set
ai_thresholds = threshold_model.predict(X_test)
ai_thresholds_rescaled = scaler.inverse_transform(ai_thresholds)

# Make Predictions
predictions = prediction_model.predict(X_test)

# Reverse scale predictions and actual values
predictions_rescaled = scaler.inverse_transform(predictions)
y_test_rescaled = scaler.inverse_transform(y_test)

# Function to analyze AI-threshold-based predictions
def analyze_predictions(actual, predicted, thresholds):
    """
    Compare predicted values against AI-generated thresholds.
    """
    results = []
    for i in range(len(actual)):
        actual_vals = actual[i]
        predicted_vals = predicted[i]
        threshold_vals = thresholds[i]

        temp, moisture, ph = predicted_vals[:3]
        th_temp, th_moisture, th_ph = threshold_vals[:3]

        msg = f"Actual: {actual_vals}, Predicted: {predicted_vals}, AI Thresholds: {threshold_vals}"

        if moisture < th_moisture:
            msg += " | Moisture Below AI Threshold!"

        if temp > th_temp:
            msg += " | Temp Above AI Threshold!"

        if ph < th_ph:
            msg += " | pH Below AI Threshold!"
        elif ph > th_ph + 1:  # +1 buffer
            msg += " | pH Above AI Threshold!"

        results.append(msg)

    return results

# Print analysis results
analysis = analyze_predictions(y_test_rescaled, predictions_rescaled, ai_thresholds_rescaled)
for msg in analysis[:5]:  # Show first 5 samples
    print(msg)