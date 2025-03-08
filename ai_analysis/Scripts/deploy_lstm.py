import numpy as np
import time
from tensorflow.keras.models import load_model
from data_preprocessing import load_and_preprocess_data

# Load trained LSTM model
model = load_model("../models/lstm_greenhouse_model.h5")

# Function to simulate live sensor data
# def get_live_sensor_data():
#     # Example format (In real case, this data should come from AWS IoT / MQTT sensors)
#     return np.random.uniform(20, 30, size=(1, 24, 4))  # Simulating 4 sensor features

def get_live_sensor_data():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    query = f"SELECT Temperature, Humidity, CO2, Soil_Moisture FROM {TABLE_NAME} ORDER BY Timestamp DESC LIMIT 24"
    df = pd.read_sql(query, conn)
    
    conn.close()
    
    # Reverse order (most recent first)
    data = df.iloc[::-1].values
    return np.expand_dims(data, axis=0)  # Reshape for model input

# Real-time prediction loop
while True:
    latest_data = get_live_sensor_data()
    predicted_values = model.predict(latest_data)

    # Convert back to original scale
    predicted_values_rescaled = scaler.inverse_transform(predicted_values)
    print("Predicted Next Hour Conditions:", predicted_values_rescaled[0])

    time.sleep(10)  # Simulate 10-second delay before next prediction