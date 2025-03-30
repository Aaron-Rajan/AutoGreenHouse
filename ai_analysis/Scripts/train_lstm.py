# Adaptive Model

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras import regularizers
from data_preprocessing import load_and_preprocess_data
import numpy as np
import json
import os

# Load preprocessed data
X_train, X_test, y_train, y_test, scaler = load_and_preprocess_data()

# Define Adaptive Threshold Model
def build_threshold_lstm():
    model = Sequential([
        LSTM(32, activation='tanh', return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
        Dropout(0.3),
        LSTM(16, activation='tanh'),
        Dropout(0.3),
        Dense(y_train.shape[1], activation="relu", kernel_regularizer=regularizers.l2(0.001))  # Predicts optimal threshold values, added L2 regularization
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

# Initialize Model
threshold_model = build_threshold_lstm()

# Early Stopping
early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
checkpoint = ModelCheckpoint("../models/adaptive_threshold_model.keras", save_best_only=True, monitor="val_loss", mode="min")

# Debugging
print("🧪 y_train Min:", y_train.min(axis=0))
print("🧪 y_train Max:", y_train.max(axis=0))


# Train Model
history = threshold_model.fit(
    X_train, y_train,
    epochs=100, batch_size=32,
    validation_data=(X_test, y_test),
    callbacks=[early_stopping, checkpoint],
    verbose=1
)

# Save the trained model
threshold_model.save("../models/adaptive_threshold_model.keras")

# Save training history
with open("../models/threshold_training_history.json", "w") as f:
    json.dump(history.history, f)

print("✅ Adaptive Threshold Model Training Complete. Model Saved.")

import joblib

# Save scaler to disk
joblib.dump(scaler, "../models/scaler.pkl")
print("✅ Scaler saved to '../models/scaler.pkl'")