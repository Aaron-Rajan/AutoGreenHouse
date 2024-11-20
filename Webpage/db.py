import sqlite3

# Create (or connect to) the database
conn = sqlite3.connect('sensor_data/temp_data.db')
conn2 = sqlite3.connect('sensor_data/ph_data.db')
conn3 = sqlite3.connect('sensor_data/co2_data.db')
conn4 = sqlite3.connect('sensor_data/moist_data.db')

# Create a cursor to execute SQL commands
cursor = conn.cursor()
cursor2 = conn2.cursor()
cursor3 = conn3.cursor()
cursor4 = conn4.cursor()

# Create the tables
# temperature data
cursor.execute('''
CREATE TABLE IF NOT EXISTS SensorData (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,    
    temperature REAL NOT NULL,
    humidity REAL NOT NULL
)
''')
# -- Unique ID for each record
# -- Date in the format 'YYYY-MM-DD'
# -- Temperature value (e.g., in Celsius)
# -- Humidity value (e.g., as a percentage)

# pH data
cursor2.execute('''
CREATE TABLE IF NOT EXISTS SensorData (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,    
    pH REAL NOT NULL
)
''')

# CO2 data
cursor3.execute('''
CREATE TABLE IF NOT EXISTS SensorData (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,    
    CO2 REAL NOT NULL
)
''')
# Soil moisture data
cursor.execute('''
CREATE TABLE IF NOT EXISTS SensorData (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,    
    soil_moist REAL NOT NULL
)
''')



# Save changes and close the connection
conn.commit()
conn.close()
conn2.commit()
conn2.close()
conn3.commit()
conn3.close()
conn4.commit()
conn4.close()

print("Database and tables created successfully.")
