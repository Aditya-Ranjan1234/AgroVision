# File: sender.py
import pandas as pd
import requests
import time
from flask import Flask
import threading

app = Flask(__name__)

# Configuration
RECEIVER_URL = "http://localhost:8002/receive"
CSV_FILE = "agriculture_with_inference.csv"
INTERVAL_SECONDS = 2

# Read CSV file
try:
    df = pd.read_csv(CSV_FILE)
except FileNotFoundError:
    print(f"Error: {CSV_FILE} not found. Ensure the file is in the same directory.")
    exit(1)

# Rename columns to match receiver's Pydantic model
df = df.rename(columns={
    'soil_moisture_%': 'soil_moisture_percent',
    'humidity_%': 'humidity_percent'
})

def send_data():
    """
    Function to send data row by row to the receiver server
    """
    for index, row in df.iterrows():
        # Convert row to dictionary, replace NaN with None
        data = row.fillna("None").to_dict()
        
        # Convert numeric fields to float to avoid type errors
        for key in ['soil_moisture_percent', 'soil_pH', 'temperature_C', 'rainfall_mm', 
                    'humidity_percent', 'sunlight_hours', 'pesticide_usage_ml', 
                    'yield_kg_per_hectare', 'latitude', 'longitude', 'NDVI_index']:
            if data[key] != "None":
                try:
                    data[key] = float(data[key])
                except (ValueError, TypeError):
                    print(f"Warning: Invalid value for {key} in row {index + 1}: {data[key]}")
                    data[key] = 0.0
        
        try:
            # Send POST request to receiver
            response = requests.post(RECEIVER_URL, json=data, timeout=5)
            if response.status_code == 200:
                print(f"Sent row {index + 1}/{len(df)}: {response.json()}")
            else:
                print(f"Failed to send row {index + 1}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error sending row {index + 1}: {e}")
        
        # Wait for the specified interval
        time.sleep(INTERVAL_SECONDS)

# Endpoint to start data sending
@app.route("/start", methods=["GET"])
def start_sending():
    thread = threading.Thread(target=send_data)
    thread.start()
    return {"message": "Started sending data"}, 200

@app.route("/")
def home():
    return {"message": "Sender server running. Use /start to begin data transfer."}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)