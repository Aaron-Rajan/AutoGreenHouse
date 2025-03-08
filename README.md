# Self-Sustaining Intelligent Greenhouse (SSIG)

## 📌 Project Overview
The **Self-Sustaining Intelligent Greenhouse (SSIG)** is an automated system designed to monitor and regulate environmental conditions to optimize plant growth. The system collects real-time data from various sensors configured with an **ESP32 microcontroller**, stores it in an **AWS-hosted MySQL database**, and provides a **Flask-based web dashboard** for visualization. 

## 🚀 Features
- **Real-Time Sensor Monitoring**: Tracks temperature, humidity, CO2 levels, TVOC, moisture, and pH.
- **Flask-Based Web Dashboard**: Displays the latest sensor data and images.
- **AWS Cloud Integration**: Stores sensor data and images in a remote MySQL database.
- **AI-Driven Analytics & Automation**: 
  - The system runs **AI analytics** on stored data from the AWS database.
  - AI-generated recommendations determine ideal environmental conditions for plant growth.
  - AI decisions send control **flags** to the **ESP32 microcontroller** to regulate conditions dynamically.
- **Automated Greenhouse Control System**:
  - **Temperature Control**: AI sends a flag to the ESP32, activating exhaust fans when needed.
  - **pH Regulation**: AI adjusts pH by triggering a **water pump** that delivers acidic or basic solutions through pipes.
  - **Soil Moisture Control**: AI ensures optimal soil moisture by activating a **water pump** to deliver water through an irrigation system.
- **Automated Image Display**: Retrieves the latest image stored in the database for visualization.

## 📂 Project Structure
```
AutoGreenHouse/
│── Arduino/
│── Webpage/
│   │── static/
│   │── templates/
│   │── app.py  # Flask server
│   │── requirements.txt  # Dependencies
│   └── README.md  # Project documentation
```

## 🛠 Technologies Used
- **Backend**: Python (Flask, SQLAlchemy, AI Analytics)
- **Database**: MySQL (AWS RDS)
- **Frontend**: HTML, CSS (TailwindCSS), Jinja2
- **Cloud Storage**: AWS RDS (Relational Database Service)
- **Libraries**: Pillow (PIL), PyMySQL, Flask-SQLAlchemy, AI-based analytics
- **Embedded System**: ESP32 (for sensor data collection & automation)
- **Actuators**: Exhaust fans, water pumps for pH and moisture control

## 📡 Sensor Data & AI-Based Automation
- **Sensor Values Collection**:
  - The **ESP32** collects data from multiple sensors measuring temperature, humidity, CO2, TVOC, soil moisture, and pH.
  - The collected values are sent to the web dashboard to display real-time changes.
- **AI-Driven Recommendations & Automation**:
  - AI **analyzes historical data** from AWS RDS to determine optimal conditions.
  - AI-generated recommendations are used to **automatically control** the greenhouse environment.
  - Control signals are sent from the AI module to the **ESP32**, which executes actions:
    - Activating **exhaust fans** for temperature regulation.
    - Adjusting **pH levels** using an acid/base solution pump.
    - Maintaining **soil moisture** by triggering a water pump for irrigation.

## 🏗 Setup & Installation
### 1️⃣ Clone the Repository
```sh
git clone https://github.com/your-repo/AutoGreenHouse.git
cd AutoGreenHouse/Webpage
```

### 2️⃣ Install Dependencies
```sh
pip install -r requirements.txt
```

### 3️⃣ Configure AWS Database Connection
Edit `app.py` and update the following variables with your AWS RDS credentials:
```python
DB_USER = "admin"
DB_PASSWORD = "your_password"
DB_HOST = "your_rds_host"
DB_NAME = "ssigdata"
```

### 4️⃣ Run the Flask Server
```sh
python app.py
```
The dashboard will be accessible at **`http://127.0.0.1:5000/`**.

## 🌱 Future Improvements
- **Advanced AI Models**: Use machine learning for predictive analytics on plant growth and early disease detection.
- **WebSocket Implementation**: Enable real-time updates without requiring page refresh.
- **Mobile App Support**: Extend accessibility via an Android/iOS application.
- **Energy Efficiency Optimization**: Implement solar power and smart energy consumption techniques.

---

💡 **Developed by:** Aaron, Karanvir, Sameer, Itraza, Inno

