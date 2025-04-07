from flask import Flask, render_template, jsonify, request, send_file, render_template_string, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import io
import mysql.connector
from PIL import Image
from sqlalchemy import text
from datetime import datetime
import secrets
import base64
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set the non-GUI 
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_analysis', 'Scripts'))

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

app = Flask(__name__)

secrets.token_hex(32)
app.secret_key = "a7fdb9328d9fa1ce0e0ba0d5b29a23fd9c2f8e469cb17bcfae3d4b1a9a4cc2b1"

# Register custom filter
@app.template_filter('b64encode')
def b64encode_filter(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ''

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

class PlantHealth(db.Model):
    __tablename__ = 'plant_health_images'  # Match your actual DB table name

    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.LargeBinary, nullable=False)
    basil_health = db.Column(db.Float)
    parsley_health = db.Column(db.Float)
    rosemary_thyme_health = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)

# In-memory storage for actuator command
latest_actuator_command = {
    "actuator": None,
    "duration": 0
}

class CaptureFlag(db.Model):
     __tablename__ = 'capture_flags'
     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
     capture_trigger = db.Column(db.Boolean, default=False)

# Secret key for session management
app.secret_key = 'your_super_secret_key_here'

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        next_page = request.form.get('next') or 'latest_prediction'
        password = request.form.get('password')

        if password == "400321812":
            session['authenticated'] = True
            return redirect(url_for(next_page))
        else:
            return render_template("login.html", error="❌ Incorrect password. Try again.")
    
    # GET request (show login form)
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

    # Auto-logout on index refresh
    session.pop('authenticated', None)

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

@app.route('/upload', methods=['POST'])
def upload_data():
    data = request.json  # Receive JSON data from ESP32
    cursor = mysql_db.cursor()

    sql = """INSERT INTO ssig_sensor_data (co2, tvoc, moisture, pH, temperature, humidity) 
             VALUES (%s, %s, %s, %s, %s, %s)"""
    values = (data["co2"], data["tvoc"], data["moisture"], data["pH"], data["temperature"], data["humidity"])

    cursor.execute(sql, values)
    mysql_db.commit()
    cursor.close()

    # ✅ Call LSTM analysis function
    try:
        from deploy_lstm import generate_and_store_prediction
        generate_and_store_prediction()
    except Exception as e:
        print("❌ LSTM analysis failed:", e)

    return jsonify({"message": "Sensor data stored and prediction triggered ✅"}), 201


@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        image_data = request.data
        cursor = mysql_db.cursor()
        sql = "INSERT INTO images (image) VALUES (%s)"
        cursor.execute(sql, (image_data,))
        mysql_db.commit()
        cursor.close()

        # ✅ Call green_label.py processing function
        from green_label import main as run_labeling
        run_labeling()

        return jsonify({"message": "Image uploaded and labeled successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
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
        return redirect(url_for('login', next='buttons_page'))

    # Render the page first, then clear session
    response = render_template("buttons.html")

    # # Clear session after rendering
    # session.pop('authenticated', None)

    return response

@app.route('/get_latest_command', methods=['GET'])
def get_latest_command():
    command = db.session.execute(
        text("""
            SELECT * FROM actuator_commands 
            WHERE executed = FALSE 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
    ).fetchone()

    if command:
        db.session.execute(
            text("UPDATE actuator_commands SET executed = TRUE WHERE id = :id"),
            {"id": command.id}
        )
        db.session.commit()
        return jsonify({
            "actuator": command.actuator_type,
            "duration": command.duration
        })

    return jsonify({"actuator": "", "duration": 0})

@app.route('/get_data', methods=['GET'])
def get_data():
    latest = db.session.query(SensorData).order_by(SensorData.timestamp.desc()).first()
    if latest:
        return jsonify({
            "moisture": latest.moisture,
            "temperature": latest.temperature,
            "pH": latest.pH
        })
    return jsonify({"moisture": 0, "temperature": 0, "pH": 7})

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

@app.route('/trigger_capture', methods=['POST'])
def trigger_capture():
    try:
        # Set trigger flag in the database
        flag = CaptureFlag.query.first()
        if not flag:
            flag = CaptureFlag(trigger=True)
            db.session.add(flag)
        else:
            flag.capture_trigger = True
        db.session.commit()
        
        return jsonify({"message": "Capture flag set!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
     
@app.route('/should_capture', methods=['GET'])
def should_capture():
    try:
        flag = CaptureFlag.query.first()
        if flag and flag.capture_trigger:
            # Reset flag after capture
            flag.capture_trigger = False
            db.session.commit()
            return jsonify({"capture": True})
        
        return jsonify({"capture": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trigger_actuator', methods=['POST'])
def trigger_actuator():
    data = request.get_json()
    actuator = data.get("actuator")
    duration = data.get("duration")

    if actuator not in ["water_pump", "acid_pump", "base_pump", "exhaust_fan"]:
        return jsonify({"error": "Invalid actuator type"}), 400

    try:
        db.session.execute(
            text("""
                INSERT INTO actuator_commands (actuator_type, duration, executed)
                VALUES (:actuator, :duration, FALSE)
            """),
            {"actuator": actuator, "duration": duration}
        )
        db.session.commit()
        return jsonify({"message": f"{actuator} command created ✅"}), 200

    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
@app.route('/predictions')
def latest_prediction():
    # Require login
    if not session.get('authenticated'):
        return redirect(url_for('login', next='latest_prediction'))

    try:
        cursor = mysql_db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM ai_predictions
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        latest_row = cursor.fetchone()
        cursor.close()

        if not latest_row:
            return render_template("predictions.html", message="⚠ No prediction data found.", prediction=None)

        return render_template("predictions.html", prediction=latest_row)

    except Exception as e:
        return f"❌ Error retrieving prediction: {str(e)}", 500


@app.route('/set_thresholds', methods=['POST'])
def set_thresholds():
    try:
        # Get values from the form
        co2 = request.form.get('co2')
        tvoc = request.form.get('tvoc')
        moisture = request.form.get('moisture')
        temperature = request.form.get('temperature')
        humidity = request.form.get('humidity')
        ph = request.form.get('ph')

        # Insert into thresholds table
        cursor = mysql_db.cursor()
        sql = """
            INSERT INTO thresholds (co2, tvoc, moisture, temperature, humidity, pH)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (co2, tvoc, moisture, temperature, humidity, ph))
        mysql_db.commit()
        cursor.close()

        flash("✅ Thresholds successfully sent!", "success")
        return redirect(url_for('latest_prediction'))
        # return redirect(url_for('latest_prediction'))  # redirect to /predictions
    except Exception as e:
        return f"❌ Error saving thresholds: {str(e)}", 500

@app.route('/get_thresholds', methods=['GET'])
def get_thresholds():
    try:
        cursor = mysql_db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM thresholds
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        latest = cursor.fetchone()
        cursor.close()

        if latest:
            return jsonify({
                "co2": latest.get("co2"),
                "tvoc": latest.get("tvoc"),
                "moisture": latest.get("moisture"),
                "temperature": latest.get("temperature"),
                "humidity": latest.get("humidity"),
                "pH": latest.get("pH"),
                "timestamp": latest.get("timestamp").isoformat() if latest.get("timestamp") else None
            })
        else:
            return jsonify({"error": "No threshold data found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_plot(df, plant_column, plant_name, color):
    fig, ax = plt.subplots(figsize=(8, 4))
    
    ax.plot(df['timestamp'], df[plant_column], marker='o', linewidth=2, color=color, label=plant_name)
    
    ax.set_title(f"{plant_name} Health Over Time", fontsize=14, fontweight='bold')
    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("Health Score (%)", fontsize=12)
    
    ax.set_ylim(0, 100)
    ax.legend()
    ax.grid(visible=True, linestyle='--', alpha=0.6)

    # Format x-axis date labels
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%Y'))
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)

    # Tight layout to prevent clipping
    plt.tight_layout()

    # Encode plot to base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)
    
    return encoded


@app.route("/health")
def health():
    latest_health = db.session.query(PlantHealth).order_by(PlantHealth.timestamp.desc()).first()
    health_records = db.session.query(PlantHealth).order_by(PlantHealth.timestamp).all()

    df = pd.DataFrame([{
        "timestamp": h.timestamp,
        "basil_health": h.basil_health,
        "parsley_health": h.parsley_health,
        "rosemary_thyme_health": h.rosemary_thyme_health
    } for h in health_records])

    # Reuse the generate_plot function as above
    basil_graph = generate_plot(df, "basil_health", "Basil", "green")
    parsley_graph = generate_plot(df, "parsley_health", "Parsley", "blue")
    rosemary_graph = generate_plot(df, "rosemary_thyme_health", "Rosemary/Thyme", "purple")

    return render_template("health.html", plant_health=latest_health,
                           basil_graph=basil_graph,
                           parsley_graph=parsley_graph,
                           rosemary_graph=rosemary_graph)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
