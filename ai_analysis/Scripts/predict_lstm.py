import numpy as np
from tensorflow.keras.models import load_model
from data_preprocessing import load_and_preprocess_data

# Load trained model
prediction_model = load_model("ai_analysis/models/adaptive_threshold_model.keras")

# Load test data
file_path = "../Data/greenhouse_sensor_data.csv"
_, X_test, _, y_test, scaler = load_and_preprocess_data(file_path)

# Make Predictions
predictions = prediction_model.predict(X_test)

# Reverse scale predictions and actual values
predictions_rescaled = scaler.inverse_transform(predictions)
y_test_rescaled = scaler.inverse_transform(y_test)

# --------------------------------------------
# Optimal Values Evaluation 
# --------------------------------------------

# Averaged ideal ranges across rosemary, oregano, basil, parsley, mint, thyme
IDEAL_CONDITIONS = {
    "co2": (300, 600),              # ppm
    "tvoc": (0, 200),               # ppb
    "moisture": (30, 60),           # % (root zone moisture)
    "temperature": (18, 27),        # °C
    "humidity": (50, 70),           # %
    "pH": (5.8, 7.0)                # pH range for herbs
}

def evaluate_against_ideal(values, label="Prediction"):
    """
    Compare a predicted or sensor value array against ideal conditions for herbs.
    """
    metrics = list(IDEAL_CONDITIONS.keys())
    messages = []
    for i, key in enumerate(metrics):
        val = values[i]
        low, high = IDEAL_CONDITIONS[key]

        if val < low:
            messages.append(f"{label} {key.upper()} too LOW ({val:.2f} < {low})")
        elif val > high:
            messages.append(f"{label} {key.upper()} too HIGH ({val:.2f} > {high})")
        else:
            messages.append(f"{label} {key.upper()} is OPTIMAL ({val:.2f})")
    return messages

def compute_health_score(values):
    """
    Compute plant health score (0–100) using softer penalties for minor deviations.
    """
    metrics = list(IDEAL_CONDITIONS.keys())
    total_score = 0

    for i, key in enumerate(metrics):
        val = values[i]
        low, high = IDEAL_CONDITIONS[key]
        center = (low + high) / 2
        range_width = (high - low) / 2
        buffer = range_width * 0.5  # Allow a 50% grace margin

        if low <= val <= high:
            score = 100  # perfect
        else:
            # Outside ideal range, apply soft penalty
            dist_from_boundary = min(abs(val - low), abs(val - high))
            penalty = min(dist_from_boundary / (range_width + buffer), 1.0)
            score = max(0, round(100 * (1 - penalty), 2))

        total_score += score

    return round(total_score / len(metrics), 2)


# Main Output Loop
if __name__ == "__main__":
    print("\n==============================")
    print("IDEAL CONDITION EVALUATION")
    print("==============================")
    for i, pred in enumerate(predictions_rescaled[:5]):
        print(f"\nSample {i+1}:")
        evaluation = evaluate_against_ideal(pred, label="Predicted")
        for msg in evaluation:
            print(" -", msg)

        # Plant Health Score
        health_score = compute_health_score(pred)
        print(f"\n PLANT HEALTH SCORE: {health_score}/100")
