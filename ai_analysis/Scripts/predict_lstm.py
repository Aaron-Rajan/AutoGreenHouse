import numpy as np
from tensorflow.keras.models import load_model
from data_preprocessing import load_and_preprocess_data

# Load trained model
model = load_model("../models/lstm_greenhouse_model.h5")

# Load test data
file_path = "../data/greenhouse_sensor_data.csv"
_, X_test, _, y_test, scaler = load_and_preprocess_data(file_path)

# Make predictions
predictions = model.predict(X_test)

# Reverse scale predictions
predictions_rescaled = scaler.inverse_transform(predictions)
y_test_rescaled = scaler.inverse_transform(y_test)

# Print sample prediction
print("Actual vs Predicted:")
for i in range(5):
    print(f"Actual: {y_test_rescaled[i]}, Predicted: {predictions_rescaled[i]}")