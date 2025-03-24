from flask import Flask, render_template, jsonify, request, send_file, render_template_string, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import io
import mysql.connector
from PIL import Image

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

# Database connection for direct queries
mysql_db = mysql.connector.connect(
    host="ssigdata.czcwce6iiq8v.ca-central-1.rds.amazonaws.com",
    user="admin",
    password="400321812",
    database="ssigdata",
    autocommit=True
)

# Define Database Model for Sensor Data
class SensorData(db.Model):
    __tablename__ = 'ssig_sensor_data'
    id = db.Column(db.Integer, primary_key=True)
    co2 = db.Column(db.Integer, nullable=True)
    tvoc = db.Column(db.Integer, nullable=True)
    moisture = db.Column(db.Integer, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    pH = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)

# Define Database Model for Images (with timestamp)
class ImageData(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.LargeBinary, nullable=False)  # BLOB storage for image data
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)

# In-memory storage for actuator command
latest_actuator_command = {
    "actuator": None,
    "duration": 0
}

# Secret key for session management
app.secret_key = 'your_super_secret_key_here'  # Replace this with something strong

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "400321812":
            session['authenticated'] = True
            return redirect(url_for('buttons_page'))
        else:
            return render_template("login.html", error="❌ Incorrect password. Try again.")
    return render_template("login.html")

# Route to fetch and display image
@app.route('/image/<int:image_id>')
def get_image(image_id):
    try:
        image_data = db.session.query(ImageData).filter_by(id=image_id).first()
        if not image_data:
            return "❌ Image not found", 404
        
        # Convert BLOB to an image and send as response
        return send_file(io.BytesIO(image_data.image), mimetype='image/jpeg')
    except Exception as e:
        return f"❌ Error retrieving image: {str(e)}", 500

# Homepage Route (Displays Latest Sensor Data and Image)
@app.route('/')
def index():
    try:
        # Fetch the most recent sensor data
        latest_sensor_data = db.session.query(SensorData).order_by(SensorData.timestamp.desc()).first()

        # Fetch the latest image (if available)
        latest_image = db.session.query(ImageData).order_by(ImageData.id.desc()).first()
        image_url = f"/image/{latest_image.id}" if latest_image else None

        if not latest_sensor_data:
            message = "⚠ No sensor data available in the database."
            return render_template("index.html", message=message, sensor_data=None, image_url=image_url)

        return render_template("index.html", sensor_data=latest_sensor_data, image_url=image_url)
    except Exception as e:
        return f"❌ Error retrieving data: {str(e)}"
    
# Route to display all collected sensor data in a table
@app.route('/data')
def display_data():
    try:
        # Fetch all sensor data from the database
        all_sensor_data = db.session.query(SensorData).order_by(SensorData.timestamp.desc()).all()

        # If no data is found, display a message
        if not all_sensor_data:
            message = "⚠ No sensor data available in the database."
            return render_template("data.html", message=message, sensor_data=None)

        # Render the data page with the sensor data
        return render_template("data.html", sensor_data=all_sensor_data)
    except Exception as e:
        return f"❌ Error retrieving sensor data: {str(e)}"

# Route to display all past images in descending order by timestamp
@app.route('/gallery')
def gallery():
    try:
        # Fetch all images from the database ordered by timestamp (most recent first)
        all_images = db.session.query(ImageData).order_by(ImageData.timestamp.desc()).all()

        # If no images are found, display a message
        if not all_images:
            message = "⚠ No images found in the database."
            return render_template("gallery.html", message=message, images=None)

        # Render the gallery page with the images
        return render_template("gallery.html", images=all_images)
    except Exception as e:
        return f"❌ Error retrieving images: {str(e)}"

@app.route('/buttons')
def buttons_page():
    if not session.get('authenticated'):
        return redirect(url_for('login'))

    # Render the page first, then clear session
    response = render_template("buttons.html")

    # Clear session after rendering
    session.pop('authenticated', None)

    return response


@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/get_actuator_command', methods=['GET'])
def get_actuator_command():
    global latest_actuator_command

    if latest_actuator_command["actuator"] is None:
        return jsonify({"actuator": "", "duration": 0})

    # Return the latest command and reset it so it's only run once
    command = latest_actuator_command.copy()
    latest_actuator_command["actuator"] = None
    latest_actuator_command["duration"] = 0

    return jsonify(command)


@app.route('/trigger_actuator', methods=['POST'])
def trigger_actuator():
    global latest_actuator_command
    try:
        data = request.get_json()
        actuator = data.get("actuator")
        level = int(data.get("level"))

        if actuator not in ["water_pump", "acid_pump", "base_pump", "exhaust_fan"]:
            return jsonify({"error": "Invalid actuator type"}), 400

        # Duration mapping
        duration_map = {1: 10, 2: 20, 3: 30}
        duration = duration_map.get(level, 10)

        # Save the latest command
        latest_actuator_command["actuator"] = actuator
        latest_actuator_command["duration"] = duration

        print(f"🔧 Command saved: {actuator} for {duration} seconds")

        return jsonify({"message": f"{actuator.replace('_', ' ').title()} triggered for {duration} seconds ✅"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
