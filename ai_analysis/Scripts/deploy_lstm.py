import pandas as pd
import numpy as np
import mysql.connector
from tensorflow.keras.models import load_model
import joblib
from datetime import datetime
from data_preprocessing import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, TABLE_NAME

# Load model and scaler
model = model = load_model("ai_analysis/models/adaptive_threshold_model.keras")
scaler = joblib.load("ai_analysis/models/scaler.pkl")

# Function to insert prediction into ai_predictions
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
        values = (now, *[float(x) for x in prediction])

        cursor.execute(insert_query, values)
        conn.commit()
        cursor.close()
        conn.close()

        print("\n SUCCESS: AI Prediction inserted into database.")
    except Exception as e:
        print("\n ERROR: Failed to insert AI prediction:", e)

# Function to get the latest 24 rows of sensor data
def get_live_sensor_data():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    query = f"""
        SELECT timestamp, co2, tvoc, moisture, temperature, humidity, pH 
        FROM {TABLE_NAME} 
        ORDER BY timestamp DESC 
        LIMIT 24
    """

    df = pd.read_sql(query, conn)
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    features = ['co2', 'tvoc', 'moisture', 'temperature', 'humidity', 'pH']
    df[features] = df[features].apply(pd.to_numeric, errors='coerce')
    df.dropna(inplace=True)
    df = df.iloc[::-1]  # Make it chronological

    return df

# Main callable function
def generate_and_store_prediction():
    df = get_live_sensor_data()

    if df.empty or len(df) < 24:
        print("\nWARNING: Not enough data for prediction.")
        return

    features = ['co2', 'tvoc', 'moisture', 'temperature', 'humidity', 'pH']
    input_data = df[features].values.astype(np.float32)

    scaled_input = scaler.transform(input_data)
    reshaped = np.expand_dims(scaled_input, axis=0)

    prediction = model.predict(reshaped)
    result = scaler.inverse_transform(prediction)[0]

    # 🌿 Display prediction nicely
    labels = ['CO2 (ppm)', 'TVOC (ppb)', 'Moisture (%)', 'Temp (°C)', 'Humidity (%)', 'pH']
    print("\nPredicted Next Hour Conditions:")
    for label, val in zip(labels, result):
        print(f"   - {label}: {val:.2f}")

    insert_prediction_to_db(result)

# Optional: test the function directly
if __name__ == "__main__":
    generate_and_store_prediction()
