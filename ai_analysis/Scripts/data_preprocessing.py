import pandas as pd
import numpy as np
import mysql.connector
from sklearn.preprocessing import MinMaxScaler

# AWS MySQL Credentials
DB_HOST = "ssigdata.czcwce6iiq8v.ca-central-1.rds.amazonaws.com"
DB_USER = "admin"
DB_PASSWORD = "400321812"  
DB_NAME = "ssigdata"
TABLE_NAME = "ssig_sensor_data"

def load_and_preprocess_data(lookback=24):
    print("Connecting to AWS MySQL...")

    # Connect to AWS MySQL
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    # Fetch data (Match column names exactly!)
    query = f"""
        SELECT timestamp, co2, tvoc, moisture, temperature, humidity, pH 
        FROM {TABLE_NAME} 
        ORDER BY timestamp ASC
    """
    df = pd.read_sql(query, conn)

    conn.close()
    print("Data fetched successfully!")

    '''Newly Added'''
    # Print Raw Data before Processing
    print("Raw Data from MySQL")
    print(df.head(10))

    # Convert timestamp to datetime and set as index
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)


    '''Newly Added'''
    df.fillna(df.median(), inplace=True)

    # Replace negative values with 0 (if needed)
    df[df < 0] = 0

    # Print cleaned data before normalization
    print("Cleaned data (Before Normalization)")
    print(df.head(10))  # Print first 10 rows after cleaning

    # Normalize sensor data (skip timestamp)
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
    return X[:split], X[split:], y[:split], y[split:], scaler

# Example usage
if __name__ == "__main__":
    X_train, X_test, y_train, y_test, scaler = load_and_preprocess_data()
    print("🔹 Sample Training Data: (After Normalization)", X_train[:5])
    print(X_train[:5])  # Print first 5 processed samples