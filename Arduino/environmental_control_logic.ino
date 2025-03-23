#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

//#define ACID_PIN 17   // Acid Pump
//#define BASE_PIN 5   // Base Pump
#define WATER_PIN 18   // Water Pump 1
#define FAN_PIN  19  

const char* ssid = "1600 Upper";
const char* password = "1600mainwest";
const char* serverUrl = "http://192.168.2.29:5000/get_data";  // Flask server URL

void setup() {
    pinMode(WATER_PIN, OUTPUT);
    pinMode(FAN_PIN, OUTPUT);
    Serial.begin(115200);

    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi...");
    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        delay(1000);
    }
    Serial.println("\nWiFi connected!");
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(serverUrl);
        int httpResponseCode = http.GET();

        if (httpResponseCode == 200) {
            String payload = http.getString();
            Serial.println("Received data: " + payload);

            // Parse JSON
            DynamicJsonDocument doc(1024);
            DeserializationError error = deserializeJson(doc, payload);

            if (error) {
                Serial.print("JSON Parsing failed: ");
                Serial.println(error.f_str());
                return;
            }

            // Extract values
            float soil_moisture = doc["moisture"] | 0.0;  
            float temperature = doc["temperature"] | 0.0; 

            Serial.print("Soil Moisture: ");
            Serial.println(soil_moisture);
            Serial.print("Temperature: ");
            Serial.println(temperature);

            // Control water pump
            if (soil_moisture < 40.0) {  // Adjust threshold as needed
                Serial.println("Turning pump ON");
                digitalWrite(WATER_PIN, HIGH);
            } else {
                Serial.println("Turning pump OFF");
                digitalWrite(WATER_PIN, LOW);
            }

            // Control fan
            if (temperature > 20.0) {  // Adjust threshold as needed
                Serial.println("Turning fan ON (Temperature too high)");
                digitalWrite(FAN_PIN, HIGH);
            } else {
                Serial.println("Turning fan OFF");
                digitalWrite(FAN_PIN, LOW);
            }
        } else {
            Serial.print("HTTP Request failed. Error code: ");
            Serial.println(httpResponseCode);
        }

        http.end();
    } else {
        Serial.println("WiFi Disconnected!");
    }

    delay(10000);  // Wait 10 seconds before checking again
}