from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # Actual sensor data should be here
    sensor_data = [
        {'id': 1, 'type': 'Temperature', 'value': '22°C', 'timestamp': '2024-10-21 14:30'},
        {'id': 2, 'type': 'Humidity', 'value': '55%', 'timestamp': '2024-10-21 14:31'},
        {'id': 3, 'type': 'Air Quality', 'value': 'Good', 'timestamp': '2024-10-21 14:32'}
    ]
    return render_template('index.html', sensor_data=sensor_data)

if __name__ == '__main__':
    app.run(debug=True)
