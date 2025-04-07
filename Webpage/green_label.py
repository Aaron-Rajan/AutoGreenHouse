import cv2
import numpy as np
from PIL import Image
import mysql.connector
import io

# --- CONFIG ---
DB_USER = "admin"
DB_PASSWORD = "400321812"
DB_HOST = "ssigdata.czcwce6iiq8v.ca-central-1.rds.amazonaws.com"
DB_NAME = "ssigdata"

def fetch_latest_image():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM images ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            return result[0]
        else:
            print("❌ No images found in database.")
            return None
    except Exception as e:
        print("❌ Database error:", e)
        return None

def calculate_health_percentage(crop):
    hsv_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    # Define healthy green (vibrant) range
    lower_healthy_green = np.array([30, 30, 30])
    upper_healthy_green = np.array([95, 255, 255])
    green_mask = cv2.inRange(hsv_crop, lower_healthy_green, upper_healthy_green)
    green_pixels = cv2.countNonZero(green_mask)

    # Define general plant area (includes yellow, light brown, dull green)
    lower_plant = np.array([20, 20, 20])
    upper_plant = np.array([100, 255, 255])
    plant_area_mask = cv2.inRange(hsv_crop, lower_plant, upper_plant)
    plant_pixels = cv2.countNonZero(plant_area_mask)

    if plant_pixels == 0:
        return 0.0  # avoid divide-by-zero

    health_ratio = (green_pixels / plant_pixels) * 100
    return round(health_ratio, 1)

def upload_image_to_database(image_bgr, basil, parsley, rosemary_thyme):
    try:
        # Encode the OpenCV image to JPEG format in memory
        _, buffer = cv2.imencode('.jpg', image_bgr)
        image_bytes = buffer.tobytes()

        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        sql = """
        INSERT INTO plant_health_images (image, basil_health, parsley_health, rosemary_thyme_health)
        VALUES (%s, %s, %s, %s)
        """
        values = (image_bytes, basil, parsley, rosemary_thyme)
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Image and health stats uploaded to database!")

    except Exception as e:
        print("❌ Upload failed:", e)


def main():
    image_bytes = fetch_latest_image()
    if not image_bytes:
        return

    # Convert to OpenCV format
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    image_np = np.array(image)
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    # Plant regions: (x, y, w, h)
    plant_regions = [
        {"label": "basil", "box": (770, 550, 1600 - 770, 1200 - 550)},
        {"label": "rosemary/thyme", "box": (425, 100, 1375 - 425, 910 - 100)},
        {"label": "parsley", "box": (0, 240, 600 - 0, 1200 - 240)}
    ]

    # Track each plant's health
    health_stats = {}

    for plant in plant_regions:
        x, y, w, h = plant["box"]
        crop = image_bgr[y:y+h, x:x+w]
        health = calculate_health_percentage(crop)
        health_stats[plant["label"]] = health

        label = f"{plant['label']} - Health: {health}%"
        cv2.rectangle(image_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(image_bgr, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Save (optional local)
    cv2.imwrite("plant_health_labeled.jpg", image_bgr)

    # Upload to DB
    upload_image_to_database(
        image_bgr,
        health_stats.get("basil"),
        health_stats.get("parsley"),
        health_stats.get("rosemary/thyme")
    )

if __name__ == "__main__":
    main()
