from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import serial
import time

app = Flask(__name__)

# AWS RDS MySQL Database Configuration
DB_USER = "admin"
DB_PASSWORD = "400321812"
DB_HOST = "ssigdata.czcwce6iiq8v.ca-central-1.rds.amazonaws.com"
DB_NAME = "ssigdata"

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define Database Model for Sensor Data
class SensorData(db.Model):
    __tablename__ = 'ssig_sensor_data'  # Ensure correct table mapping

    id = db.Column(db.Integer, primary_key=True)
    co2 = db.Column(db.Integer, nullable=True)
    tvoc = db.Column(db.Integer, nullable=True)
    moisture = db.Column(db.Integer, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    pH = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)

# Homepage Route (Displays Latest Sensor Data)
@app.route('/')
def index():
    try:
        connected = True

        # Fetch the most recent row based on timestamp
        latest_sensor_data = db.session.query(SensorData).order_by(SensorData.timestamp.desc()).first()

        if not latest_sensor_data:
            message = "⚠ No sensor data available in the database."
            return render_template("index.html", message=message, sensor_data=None)

        # Pass single sensor_data object (not a list)
        return render_template("index.html", connected=connected, sensor_data=latest_sensor_data)

    except Exception as e:
        return f"❌ Error retrieving data: {str(e)}"

# API Route to Get Latest Sensor Data (Most Recent Row)
@app.route('/api/sensor', methods=['GET'])
def get_latest_sensor_data():
    try:
        # Fetch the most recent row based on timestamp
        latest_sensor_data = db.session.query(SensorData).order_by(SensorData.timestamp.desc()).first()

        if not latest_sensor_data:
            return jsonify({"error": "No sensor data found"}), 404

        data = {
            "id": latest_sensor_data.id,
            "co2": latest_sensor_data.co2,
            "tvoc": latest_sensor_data.tvoc,
            "moisture": latest_sensor_data.moisture,
            "temperature": latest_sensor_data.temperature,
            "humidity": latest_sensor_data.humidity,
            "pH": latest_sensor_data.pH,
            "timestamp": latest_sensor_data.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
