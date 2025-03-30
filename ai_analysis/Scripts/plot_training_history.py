import json
import matplotlib.pyplot as plt
import os
import numpy as np

# Select your history file
history_file = "../models/threshold_training_history.json"

if not os.path.exists(history_file):
    raise FileNotFoundError(f"Could not find history file: {history_file}")

with open(history_file, "r") as f:
    history = json.load(f)

loss = np.array(history.get("loss", []))
val_loss = np.array(history.get("val_loss", []))
epochs = np.arange(1, len(loss) + 1)

# Optional: smooth curves using moving average (window=2)
def smooth_curve(data, weight=0.8):
    smoothed = []
    last = data[0]
    for point in data:
        smoothed_val = last * weight + (1 - weight) * point
        smoothed.append(smoothed_val)
        last = smoothed_val
    return smoothed

# Plot
plt.figure(figsize=(12, 6))
plt.plot(epochs, smooth_curve(loss), label='Smoothed Training Loss', color='royalblue', linewidth=2)
plt.plot(epochs, smooth_curve(val_loss), label='Smoothed Validation Loss', color='darkorange', linewidth=2)

# Highlight minimum val_loss
min_val_idx = np.argmin(val_loss)
plt.scatter(epochs[min_val_idx], val_loss[min_val_idx], color='red', zorder=5)
plt.annotate(f"Lowest Val Loss: {val_loss[min_val_idx]:.4f}",
             xy=(epochs[min_val_idx], val_loss[min_val_idx]),
             xytext=(epochs[min_val_idx] + 1, val_loss[min_val_idx] + 0.01),
             arrowprops=dict(arrowstyle="->", color="gray"))

# Final formatting
plt.title("Smoothed Training vs Validation Loss Curve", fontsize=14)
plt.xlabel("Epoch", fontsize=12)
plt.ylabel("Loss (MSE)", fontsize=12)
plt.legend()
plt.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()
# Optional: Save plot
# plt.savefig("../models/training_loss_plot.png", dpi=300)
plt.show()