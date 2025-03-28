import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from data_preprocessing import load_and_preprocess_data
import json

# Load preprocessed data
file_path = "C:/Users/innop/Documents/School/McMaster/Semesters/Fall Term 2024/4OI6/ai_analysis/Data/greenhouse_sensor_data.csv"
X_train, X_test, y_train, y_test, scaler = load_and_preprocess_data(file_path)

# Function to build LSTM model
def build_lstm_model(input_shape):
    model = Sequential([
        LSTM(50, activation='relu', return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(50, activation='relu'),
        Dropout(0.2),
        Dense(X_train.shape[2])
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

# Initialize model
model = build_lstm_model((X_train.shape[1], X_train.shape[2]))

# Callbacks for early stopping and best model saving
early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
checkpoint = ModelCheckpoint("../models/best_lstm_model.h5", save_best_only=True, monitor="val_loss", mode="min")

# Train model
history = model.fit(
    X_train, y_train, 
    epochs=50, batch_size=16, 
    validation_data=(X_test, y_test), 
    callbacks=[early_stopping, checkpoint], 
    verbose=1
)

# Save final model
model.save("../models/lstm_greenhouse_model.keras")

# Save training history for analysis
with open("../models/training_history.json", "w") as f:
    json.dump(history.history, f)

print("Model training complete. Best model saved as 'best_lstm_model.keras'.")