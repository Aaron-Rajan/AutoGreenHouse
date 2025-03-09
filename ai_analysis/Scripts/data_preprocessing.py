# import pandas as pd
# import numpy as np
# import mysql.connector
# from sklearn.preprocessing import MinMaxScaler
# set DB_PASSWORD = 400321812
# # AWS MySQL Credentials
# DB_HOST = "ssigdata.czcwce6iiq8v.ca-central-1.rds.amazonaws.com"
# DB_USER = "admin"
# DB_PASSWORD = "400321812"  
# DB_NAME = "ssigdata"
# TABLE_NAME = "ssig_sensor_data"

# def load_and_preprocess_data(lookback=24):

#     # Convert lookback to int
#     lookback = int(lookback)
#     print("Connecting to AWS MySQL...")

#     # Connect to AWS MySQL
#     conn = mysql.connector.connect(
#         host=DB_HOST,
#         user=DB_USER,
#         password=DB_PASSWORD,
#         database=DB_NAME
#     )

#     # Fetch data (Match column names exactly!)
#     query = f"""
#         SELECT timestamp, co2, tvoc, moisture, temperature, humidity, pH 
#         FROM {TABLE_NAME} 
#         ORDER BY timestamp ASC
#     """
#     df = pd.read_sql(query, conn)

#     conn.close()
#     print("Data fetched successfully!")

#     '''Newly Added'''
#     # Print Raw Data before Processing
#     print("Raw Data from MySQL")
#     print(df.head(10))

#     # Convert timestamp to datetime and set as index
#     df['timestamp'] = pd.to_datetime(df['timestamp'])
#     df.set_index('timestamp', inplace=True)


#     '''Newly Added'''
#     df.fillna(df.median(), inplace=True)

#     # Replace negative values with 0 (if needed)
#     #df[df < 0] = 0
#     df = df.clip(lower=0)


#     # Print cleaned data before normalization
#     print("Cleaned data (Before Normalization)")
#     print(df.head(10))  # Print first 10 rows after cleaning

#     # Normalize sensor data (skip timestamp)
#     scaler = MinMaxScaler(feature_range=(0, 1))
#     scaled_data = scaler.fit_transform(df)

#     # Convert data into sequences for LSTM
#     def create_sequences(data, lookback):
#         X, y = [], []
#         for i in range(len(data) - lookback):
#             X.append(data[i:i + lookback])
#             y.append(data[i + lookback])
#         return np.array(X), np.array(y)

#     # Create time-series sequences
#     X, y = create_sequences(scaled_data, lookback)

#     # Split into training (80%) and testing (20%) sets
#     split = int(len(X) * 0.8)
#     return X[:split], X[split:], y[:split], y[split:], scaler

# # Example usage
# if __name__ == "__main__":
#     X_train, X_test, y_train, y_test, scaler = load_and_preprocess_data()
#     print("🔹 Sample Training Data: (After Normalization)", X_train[:5])
#     print(X_train[:5])  # Print first 5 processed samples

import os
import logging
import pandas as pd
import numpy as np
import mysql.connector
from sklearn.preprocessing import MinMaxScaler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS MySQL Credentials (Secure using environment variables)
DB_HOST = os.getenv("DB_HOST", "ssigdata.czcwce6iiq8v.ca-central-1.rds.amazonaws.com")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD")  # Retrieve from environment variable
DB_NAME = os.getenv("DB_NAME", "ssigdata")
TABLE_NAME = "ssig_sensor_data"

def load_and_preprocess_data(lookback=24):
    #lookback = int(lookback)  # Ensure `lookback` is an integer
    lookback = int(os.getenv("LOOKBACK", 24))

    logger.info("🔄 Connecting to AWS MySQL...")

   
    if not DB_PASSWORD:
        raise ValueError("❌ ERROR: Database password not set! Use `set DB_PASSWORD=your_actual_password` (Windows) or `export DB_PASSWORD='your_actual_password'` (Mac/Linux).")

    print(f"✅ DB_PASSWORD Loaded: {DB_PASSWORD}")  # Debugging

    # Connect to AWS MySQL using `mysql.connector`
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,  # ✅ Ensure password is passed
        database=DB_NAME
    )

    # Fetch data from MySQL
    query = f"""
        SELECT timestamp, co2, tvoc, moisture, temperature, humidity, pH 
        FROM {TABLE_NAME} 
        ORDER BY timestamp ASC
    """
    df = pd.read_sql(query, conn)

    # Close the MySQL connection
    conn.close()
    logger.info("✅ Data fetched successfully!")

    # Debugging: Show raw data
    logger.info("🔹 Raw Data from MySQL:")
    logger.info(df.head(10))

    # Convert timestamp to datetime and set as index
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    # Handle missing values
    df.fillna(df.median(), inplace=True)  # Fill NaNs with column medians
    df = df.clip(lower=0)  # Replace negative values with 0

    # Debugging: Show cleaned data
    logger.info("🔹 Cleaned Data (Before Normalization):")
    logger.info(df.head(10))

    # Normalize sensor data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df)

    # Convert data into sequences for LSTM
    def create_sequences(data, lookback):
        X, y = [], []
        for i in range(len(data) - lookback):
            X.append(data[i:i + lookback])
            y.append(data[i + lookback])
        return np.array(X), np.array(y)

    # Create time-series sequences
    X, y = create_sequences(scaled_data, lookback)

    # Split into training (80%) and testing (20%) sets
    split = int(len(X) * 0.8)
    
    logger.info(f"✅ Data Preprocessing Complete! Train Samples: {len(X[:split])}, Test Samples: {len(X[split:])}")

    return X[:split], X[split:], y[:split], y[split:], scaler

# Example usage
if __name__ == "__main__":
    X_train, X_test, y_train, y_test, scaler = load_and_preprocess_data()
    logger.info("🔹 Sample Training Data (After Normalization):")
    logger.info(X_train[:5])  # Print first 5 processed samples