# File: receiver.py
from fastapi import FastAPI
import pandas as pd
from pydantic import BaseModel
import os

app = FastAPI()

# Pydantic model to validate incoming data
class FarmData(BaseModel):
    farm_id: str
    region: str
    crop_type: str
    soil_moisture_percent: float
    soil_pH: float
    temperature_C: float
    rainfall_mm: float
    humidity_percent: float
    sunlight_hours: float
    irrigation_type: str | None
    fertilizer_type: str
    pesticide_usage_ml: float
    sowing_date: str
    harvest_date: str
    total_days: int
    yield_kg_per_hectare: float
    sensor_id: str
    timestamp: str
    latitude: float
    longitude: float
    NDVI_index: float
    crop_disease_status: str | None
    inference: str

# Initialize list to store received data
received_data = []

# Output CSV file
OUTPUT_CSV = "received_agriculture_data.csv"

@app.post("/receive")
async def receive_data(data: FarmData):
    """
    Endpoint to receive data from the sender server
    """
    # Convert received data to dictionary
    data_dict = data.dict()
    
    # Append to list
    received_data.append(data_dict)
    
    # Save to CSV
    df = pd.DataFrame([data_dict])
    if not os.path.exists(OUTPUT_CSV):
        df.to_csv(OUTPUT_CSV, index=False)
    else:
        df.to_csv(OUTPUT_CSV, mode='a', header=False, index=False)
    
    print(f"Received data for farm_id: {data.farm_id}")
    return {"message": f"Data received for farm_id: {data.farm_id}"}

@app.get("/")
async def home():
    return {"message": "Receiver server running. Send data to /receive."}

@app.get("/data")
async def get_data():
    """
    Endpoint to retrieve all received data (for frontend)
    """
    if received_data:
        return received_data
    return {"message": "No data received yet"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)