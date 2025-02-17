from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import serial
import time

app = Flask(__name__)

# AWS RDS MySQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:400321812@ssigdata.czcwce6iiq8v.ca-central-1.rds.amazonaws.com/ssigdata'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define Database Model for Sensor Data
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)

# Function to Check Microcontroller Connection
def is_microcontroller_connected(port, baud_rate=9600, timeout=1):
    try:
        ser = serial.Serial(port, baud_rate, timeout=timeout)
        ser.write(b'ping')  # Replace with appropriate message for your device
        time.sleep(0.1)
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            ser.close()
            return bool(response)
        ser.close()
        return False
    except serial.SerialException:
        return False

@app.route('/')
def index():
    port = 'COM3'  # Update with the correct port
    connected = is_microcontroller_connected(port)

    # Fetching sensor data from AWS RDS MySQL
    sensor_data = SensorData.query.order_by(SensorData.timestamp.desc()).limit(10).all()  # Get latest 10 readings

    return render_template("index.html", connected=connected, sensor_data=sensor_data)

if __name__ == '__main__':
    app.run(debug=True)
