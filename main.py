from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import random
import asyncio
from pymongo import MongoClient
import os
from typing import List, Dict
from urllib.parse import quote_plus

app = FastAPI()

# MongoDB configuration from environment variables
username = quote_plus(os.getenv("MONGODB_USERNAME", "username"))
password = quote_plus(os.getenv("MONGODB_PASSWORD", "password"))
cluster_url = os.getenv("MONGODB_CLUSTER_URL", "cluster0.mongodb.net")
db_name = os.getenv("MONGODB_DB_NAME", "meter_data")

# Initialize MongoDB client
try:
    client = MongoClient(
        f"mongodb+srv://{username}:{password}@{cluster_url}/{db_name}?retryWrites=true&w=majority",
        serverSelectionTimeoutMS=5000
    )
    # Test the connection
    client.admin.command('ping')
    db = client[db_name]
    collection = db["meter_readings"]
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    client = None
    collection = None

# In-memory storage
kvah_counter = 637000.0
latest_data = {}
current_day_data: List[Dict] = []
current_day = datetime.utcnow().date()

async def generate_data():
    global kvah_counter, latest_data, current_day_data, current_day
    
    while True:
        await asyncio.sleep(random.randint(5, 15))  # 5-15 seconds for testing
        
        current_time = datetime.utcnow()
        today = current_time.date()
        
        # Check if day has changed
        if today != current_day:
            if current_day_data and collection:
                try:
                    collection.insert_one({
                        "date": current_day.strftime("%Y-%m-%d"),
                        "readings": current_day_data,
                        "total_kvah": kvah_counter,
                        "created_at": datetime.utcnow()
                    })
                    print(f"Saved {len(current_day_data)} readings for {current_day}")
                except Exception as e:
                    print(f"Failed to save data: {e}")
            
            # Reset for new day
            current_day_data = []
            current_day = today
        
        # Generate new data
        kvah_counter += round(random.uniform(0.5, 5.0), 3)
        
        new_reading = {
            "serial_no": "131313",
            "kvah": f"{kvah_counter:.3f}",
            "instant_kva": f"{random.uniform(50, 200):.3f}",
            "voltages": {
                "r": f"{random.uniform(220, 240):.2f}",
                "y": f"{random.uniform(220, 240):.2f}",
                "b": f"{random.uniform(220, 240):.2f}"
            },
            "currents": {
                "r": f"{random.uniform(40, 230):.2f}",
                "y": f"{random.uniform(40, 230):.2f}",
                "b": f"{random.uniform(40, 230):.2f}"
            },
            "timestamp": current_time.isoformat(),
            "signal_strength": random.randint(20, 35)
        }
        
        latest_data = new_reading
        current_day_data.append(new_reading.copy())
        print(f"Generated new reading at {current_time}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(generate_data())

@app.on_event("shutdown")
async def shutdown_event():
    if client:
        client.close()

@app.get("/live")
async def get_live_data():
    """Get the latest meter reading"""
    return latest_data

@app.get("/today")
async def get_today_data():
    """Get all readings for the current day"""
    return {
        "date": current_day.strftime("%Y-%m-%d"),
        "count": len(current_day_data),
        "readings": current_day_data
    }

@app.get("/history/{date}")
async def get_history(date: str):
    """Get historical data for a specific date (YYYY-MM-DD)"""
    if not collection:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        data = collection.find_one({"date": date}, {"_id": 0})
        return data if data else {"message": "No data found for this date"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))