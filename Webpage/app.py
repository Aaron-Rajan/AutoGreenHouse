from flask import Flask, render_template, jsonify, request, send_file, render_template_string
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

#Database connection for direct queries
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

class CaptureFlag(db.Model):
    __tablename__ = 'capture_flags'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    capture_trigger = db.Column(db.Boolean, default=False)

class WaterPumpFlag(db.Model):
    __tablename__ = 'water_pump_flags'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    water_pump_trigger = db.Column(db.Boolean, default=False)

class AcidPumpFlag(db.Model):
    __tablename__ = 'acid_pump_flags'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    acid_pump_trigger = db.Column(db.Boolean, default=False)

class BasePumpFlag(db.Model):
    __tablename__ = 'base_pump_flags'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_pump_trigger = db.Column(db.Boolean, default=False)

class ExhaustFanFlag(db.Model):
    __tablename__ = 'exhaust_fan_flags'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exhaust_fan_trigger = db.Column(db.Boolean, default=False)

# Define Database Model for Images
class ImageData(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.LargeBinary, nullable=False)  # BLOB storage for image data

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
        connected = True

        # Fetch the most recent sensor data
        latest_sensor_data = db.session.query(SensorData).order_by(SensorData.timestamp.desc()).first()

        # Fetch the latest image (if available)
        latest_image = db.session.query(ImageData).order_by(ImageData.id.desc()).first()
        image_url = f"/image/{latest_image.id}" if latest_image else None

        if not latest_sensor_data:
            message = "⚠ No sensor data available in the database."
            return render_template("index.html", message=message, sensor_data=None, image_url=image_url)

        return render_template("index.html", connected=connected, sensor_data=latest_sensor_data, image_url=image_url)
    except Exception as e:
        return f"❌ Error retrieving data: {str(e)}"
    
# Route to display all collected sensor data in a table
@app.route('/data')
def display_data():
    try:
        all_sensor_data = db.session.query(SensorData).order_by(SensorData.timestamp.desc()).all()
        return render_template("data.html", sensor_data=all_sensor_data)
    except Exception as e:
        return f"❌ Error retrieving data: {str(e)}"
    
@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        # Fetch the latest sensor data row
        latest_row = db.session.query(SensorData).order_by(SensorData.timestamp.desc()).first()

        # Return as JSON
        return jsonify({
            "id": latest_row.id,
            "co2": latest_row.co2,
            "tvoc": latest_row.tvoc,
            "moisture": latest_row.moisture,
            "temperature": latest_row.temperature,
            "humidity": latest_row.humidity,
            "pH": latest_row.pH,
            "timestamp": latest_row.timestamp
        }) if latest_row else jsonify({"error": "No data available"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
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
    
    return jsonify({"message": "Sensor data stored successfully!"}), 201

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        image_data = request.data  # Get raw image data
        
        if not image_data:
            return jsonify({"error": "No image received"}), 400

        cursor = mysql_db.cursor()
        sql = "INSERT INTO images (image) VALUES (%s)"
        cursor.execute(sql, (image_data,))
        mysql_db.commit()
        cursor.close()

        return jsonify({"message": "Image uploaded successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    
@app.route('/trigger_water_pump', methods=['POST'])
def trigger_water_pump():
    flag = WaterPumpFlag.query.first()
    if not flag:
        flag = WaterPumpFlag(water_pump_trigger=True)
        db.session.add(flag)
    else:
        flag.water_pump_trigger = True
    db.session.commit()
    return jsonify({"message": "Water pump trigger set!"}), 200

@app.route('/trigger_acid_pump', methods=['POST'])
def trigger_acid_pump():
    flag = AcidPumpFlag.query.first()
    if not flag:
        flag = AcidPumpFlag(acid_pump_trigger=True)
        db.session.add(flag)
    else:
        flag.acid_pump_trigger = True
    db.session.commit()
    return jsonify({"message": "Acid pump trigger set!"}), 200

@app.route('/trigger_base_pump', methods=['POST'])
def trigger_base_pump():
    flag = BasePumpFlag.query.first()
    if not flag:
        flag = BasePumpFlag(base_pump_trigger=True)
        db.session.add(flag)
    else:
        flag.base_pump_trigger = True
    db.session.commit()
    return jsonify({"message": "Base pump trigger set!"}), 200

@app.route('/trigger_exhaust_fan', methods=['POST'])
def trigger_exhaust_fan():
    flag = ExhaustFanFlag.query.first()
    if not flag:
        flag = ExhaustFanFlag(exhaust_fan_trigger=True)
        db.session.add(flag)
    else:
        flag.exhaust_fan_trigger = True
    db.session.commit()
    return jsonify({"message": "Exhaust fan trigger set!"}), 200

@app.route('/should_trigger_water_pump', methods=['GET'])
def should_trigger_water_pump():
    flag = WaterPumpFlag.query.first()
    if flag and flag.water_pump_trigger:
        flag.water_pump_trigger = False
        db.session.commit()
        return jsonify({"trigger": True})
    return jsonify({"trigger": False})

@app.route('/should_trigger_acid_pump', methods=['GET'])
def should_trigger_acid_pump():
    flag = AcidPumpFlag.query.first()
    if flag and flag.acid_pump_trigger:
        flag.acid_pump_trigger = False
        db.session.commit()
        return jsonify({"trigger": True})
    return jsonify({"trigger": False})

@app.route('/should_trigger_base_pump', methods=['GET'])
def should_trigger_base_pump():
    flag = BasePumpFlag.query.first()
    if flag and flag.base_pump_trigger:
        flag.base_pump_trigger = False
        db.session.commit()
        return jsonify({"trigger": True})
    return jsonify({"trigger": False})

@app.route('/should_trigger_exhaust_fan', methods=['GET'])
def should_trigger_exhaust_fan():
    flag = ExhaustFanFlag.query.first()
    if flag and flag.exhaust_fan_trigger:
        flag.exhaust_fan_trigger = False
        db.session.commit()
        return jsonify({"trigger": True})
    return jsonify({"trigger": False})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
