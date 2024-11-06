from flask import Flask, render_template
import serial
import time

app = Flask(__name__)

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
    # Actual sensor data should be here
    sensor_data = [
        {'id': 1, 'type': 'Temperature', 'value': '22°C', 'timestamp': '2024-10-21 14:30'},
        {'id': 2, 'type': 'Humidity', 'value': '55%', 'timestamp': '2024-10-21 14:31'},
        {'id': 3, 'type': 'Air Quality', 'value': 'Good', 'timestamp': '2024-10-21 14:32'}
    ]
    return render_template("index.html", connected=connected, sensor_data=sensor_data)

if __name__ == '__main__':
    app.run(debug=True)
