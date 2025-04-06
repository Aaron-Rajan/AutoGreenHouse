# ===========================================
# LSTM Deployment Script for Real-Time Prediction
# -------------------------------------------
# This script connects to a MySQL database,
# checks for newly updated sensor data every 30 seconds,
# and runs predictions using a pre-trained LSTM model.
# It avoids reprocessing duplicate data by tracking timestamps.
# ===========================================

import pandas as pd
import numpy as np
import time
import mysql.connector
from tensorflow.keras.models import load_model
import joblib
from datetime import datetime  # For timestamp
from data_preprocessing import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, TABLE_NAME

# =============================
# Load pre-trained components
# =============================

# Load trained LSTM model for environmental prediction
model = load_model("../models/adaptive_threshold_model.keras")

# Load the data scaler used during training to ensure consistency
scaler = joblib.load("../models/scaler.pkl")

# Initialize the last seen timestamp (used to detect new sensor entries)
last_timestamp = None

# =============================
# Function to insert prediction into ai_predictions table
# =============================
def insert_prediction_to_db(prediction):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO ai_predictions (
                timestamp, co2, tvoc, moisture, temperature, humidity, pH
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        now = datetime.now()
        values = (now, *[float(x) for x in prediction]) # convert np.float32 -> float

        cursor.execute(insert_query, values)
        conn.commit()
        cursor.close()
        conn.close()

        print("\nAI Prediction inserted into database.\n")
    except Exception as e:
        print("\nFailed to insert AI prediction:", e)

# =============================
# Function to retrieve latest 24 sensor entries from the database
# =============================
def get_live_sensor_data():
    # Establish database connection
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    # Query to retrieve the 24 most recent sensor entries (LSTM lookback window)
    query = f"""
        SELECT timestamp, co2, tvoc, moisture, temperature, humidity, pH 
        FROM {TABLE_NAME} 
        ORDER BY timestamp DESC 
        LIMIT 24
    """

    # Fetch data into a pandas DataFrame
    df = pd.read_sql(query, conn)
    conn.close()  # Always close the connection

    # Convert timestamp column properly and preserve it
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # ONLY apply to features (avoid converting timestamp to int!)
    features = ['co2', 'tvoc', 'moisture', 'temperature', 'humidity', 'pH']
    df[features] = df[features].apply(pd.to_numeric, errors='coerce')

    df.dropna(inplace=True)
    df = df.iloc[::-1]  # Optional: Reverse to chronological order

    print("\nLatest timestamp in DataFrame:", df['timestamp'].max())

    return df

# =============================
# Real-time prediction loop
# =============================
while True:
    # Fetch the latest 24 sensor records
    df = get_live_sensor_data()

    # Extract the most recent timestamp in the fetched data
    current_latest_time = df['timestamp'].iloc[-1]

    # Check if new data has been inserted
    if current_latest_time != last_timestamp:
        # Update last seen timestamp
        last_timestamp = current_latest_time

        # Extract features in the same order used during training
        features = ['co2', 'tvoc', 'moisture', 'temperature', 'humidity', 'pH']
        input_data = df[features].values.astype(np.float32)

        # Normalize the input using the original training scaler
        scaled_input = scaler.transform(input_data)

        # Reshape to match LSTM input shape: (batch_size, time_steps, features)
        reshaped = np.expand_dims(scaled_input, axis=0)  # shape = (1, 24, 6)

        # Make prediction for the next hour's environmental conditions
        prediction = model.predict(reshaped)

        # Inverse-transform the result back to real-world scale
        result = scaler.inverse_transform(prediction)[0]

        # Display the prediction
        labels = ['CO2 (ppm)', 'TVOC (ppb)', 'Moisture (%)', 'Temp (°C)', 'Humidity (%)', 'pH']
        print("\nPredicted Next Hour Conditions:")
        for label, val in zip(labels, result):
            print(f"   - {label}: {val:.2f}")

        # Insert the prediction into ai_predictions table
        insert_prediction_to_db(result)

    else:
        # No new sensor data inserted yet
        print("\nNo new data yet... waiting")

    # Wait before rechecking (sync with 15-min sensor update cycle)
    time.sleep(30)