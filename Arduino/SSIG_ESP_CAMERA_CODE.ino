#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi Credentials (Replace with your WiFi details)
const char* ssid = "SAMEER";
const char* password = "gS19*430";

// Flask server URL (Replace with your actual server IP)
const char* serverUrl = "http://15.222.245.211:5000/upload_image"; 

// Camera pin configurations for WROVER_KIT or ESP32-CAM (Adjust if needed)
#define PWDN_GPIO_NUM    -1
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM    21
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27

#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      19
#define Y4_GPIO_NUM      18
#define Y3_GPIO_NUM      5
#define Y2_GPIO_NUM      4
#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22

// Change this pin if your ESP32-CAM board uses a different flash LED pin
#define FLASH_GPIO_NUM   4  

void startCamera() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_UXGA;  
    config.jpeg_quality = 8;
    config.fb_count = 1;

    if (esp_camera_init(&config) != ESP_OK) {
        Serial.println("❌ Camera initialization failed!");
        return;
    }
    Serial.println("✅ Camera initialized successfully!");
}

void setup() {
    Serial.begin(115200);
    WiFi.disconnect(true);
    delay(1000);

    WiFi.begin(ssid, password);
    
    Serial.print("Connecting to hotspot...");
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println("\n✅ Connected to Hotspot!");

    pinMode(FLASH_GPIO_NUM, OUTPUT); // Initialize flash GPIO
    digitalWrite(FLASH_GPIO_NUM, LOW); // Make sure the flash is off initially

    startCamera();
}

unsigned long lastAutoCaptureTime = 0;
const unsigned long autoCaptureInterval = 20000; // 20 seconds

void loop() {
    unsigned long currentTime = millis();

    // 🔍 Check for manual trigger every 5 seconds
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin("http://15.222.245.211:5000/should_capture"); 
        int httpResponseCode = http.GET();

        if (httpResponseCode == 200) {
            String response = http.getString();
            Serial.println("📥 Server Response: " + response);

            StaticJsonDocument<200> doc;
            DeserializationError error = deserializeJson(doc, response);

            if (!error) {
                bool capture = doc["capture"];
                if (capture) {
                    Serial.println("📸 Capture triggered by server!");
                    takeAndUploadPicture();
                }
            } else {
                Serial.println("❌ Failed to parse JSON response");
            }
        }

        http.end();
    }

    // ✅ Automatic capture every 20 seconds
    if (currentTime - lastAutoCaptureTime > autoCaptureInterval) {
        Serial.println("⏲ Auto capture time reached. Capturing image...");
        takeAndUploadPicture();
        lastAutoCaptureTime = currentTime;
    }

    delay(5000); // Loop runs every 5 seconds
}

void takeAndUploadPicture() {
    // Turn on flash if needed (optional)
    digitalWrite(FLASH_GPIO_NUM, HIGH);
    delay(500); // Give flash time to turn on

    camera_fb_t *fb = esp_camera_fb_get();
    digitalWrite(FLASH_GPIO_NUM, LOW); // Turn off flash after capture

    if (!fb) {
        Serial.println("❌ Camera capture failed!");
        return;
    }

    Serial.println("✅ Image Captured! Uploading...");
    HTTPClient uploadHttp;
    uploadHttp.begin(serverUrl);
    uploadHttp.addHeader("Content-Type", "image/jpeg");
    uploadHttp.POST(fb->buf, fb->len);
    uploadHttp.end();
    esp_camera_fb_return(fb);
}
