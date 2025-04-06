import pandas as pd
import matplotlib.pyplot as plt
import mysql.connector
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os


DB_HOST = os.getenv("DB_HOST", "ssigdata.czcwce6iiq8v.ca-central-1.rds.amazonaws.com")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD") 
DB_NAME = os.getenv("DB_NAME", "ssigdata")

if not DB_PASSWORD:
    raise ValueError("ERROR: Database password not set! Use `export DB_PASSWORD='your_pw'` before running.")

# Connect to AWS MySQL
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

# Query sensor and prediction data
query_sensor = """
    SELECT timestamp, temperature, humidity, moisture, pH
    FROM ssig_sensor_data
    WHERE timestamp >= NOW() - INTERVAL 1 DAY
    ORDER BY timestamp ASC
"""
query_pred = """
    SELECT timestamp, temperature, humidity, moisture, pH
    FROM ai_predictions
    WHERE timestamp >= NOW() - INTERVAL 1 DAY
    ORDER BY timestamp ASC
"""

df_sensor = pd.read_sql(query_sensor, conn)
df_pred = pd.read_sql(query_pred, conn)
conn.close()

df_sensor['timestamp'] = pd.to_datetime(df_sensor['timestamp'])
df_pred['timestamp'] = pd.to_datetime(df_pred['timestamp'])

# Plot comparison
fig, axs = plt.subplots(2, 2, figsize=(16, 10))
axs = axs.flatten()
features = ['temperature', 'humidity', 'moisture', 'pH']

for i, feature in enumerate(features):
    axs[i].plot(df_sensor['timestamp'], df_sensor[feature], label='Sensor', color='steelblue')
    axs[i].plot(df_pred['timestamp'], df_pred[feature], label='Predicted', color='orange', linestyle='--')
    axs[i].set_title(f"{feature.capitalize()} – Sensor vs AI Predicted")
    axs[i].set_xlabel("Timestamp")
    axs[i].set_ylabel(feature.capitalize())
    axs[i].legend()
    axs[i].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

plt.tight_layout()
plt.show()
