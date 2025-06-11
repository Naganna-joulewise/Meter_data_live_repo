from fastapi import FastAPI
from datetime import datetime, timedelta
import random
import asyncio
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from typing import List, Dict
from urllib.parse import quote_plus  # Add this import



app = FastAPI()


username = quote_plus("kethavaram")  # Encode username
password = quote_plus("Naganna890@")  # Encode password
cluster_url = "cluster0.gtaowbx.mongodb.net/"
db_name = "meter_data"

MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster_url}/{db_name}?retryWrites=true&w=majority"
# MongoDB configuration
# MONGO_URI = os.getenv("MONGODB_URI", "mongodb+srv://kethavaram:Naganna890@@cluster0.gtaowbx.mongodb.net/")
# DB_NAME = "meter_data"
COLLECTION_NAME = "daily_readings"

# Initialize MongoDB client
# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI)
    db = client[db_name]
    collection = db["COLLECTION_NAME"]
    client.admin.command('ping')  # Test connection
    print("Successfully connected to MongoDB!")
except ConnectionFailure as e:
    print("Could not connect to MongoDB:", e)

# In-memory storage
kvah_counter = 637000.0
latest_data = {}
current_day_data: List[Dict] = []
current_day = datetime.utcnow().date()

async def generate_data_forever():
    global kvah_counter, latest_data, current_day_data, current_day

    while True:
        wait_seconds = random.randint(60, 600)  # 1 to 10 minutes
        await asyncio.sleep(wait_seconds)

        current_time = datetime.utcnow()
        today = current_time.date()

        # Check if day has changed
        if today != current_day:
            # Store previous day's data in MongoDB
            if current_day_data:
                try:
                    collection.insert_one({
                        "date": current_day.strftime("%Y-%m-%d"),
                        "readings": current_day_data,
                        "total_kvah": kvah_counter
                    })
                    print(f"Stored {len(current_day_data)} readings for {current_day}")
                except Exception as e:
                    print("Failed to store data in MongoDB:", e)
            
            # Reset for new day
            current_day_data = []
            current_day = today

        # Generate new data
        kvah_counter += round(random.uniform(0.5, 5.0), 3)

        latest_data = {
            "serial_no": "131313",
            "kvah": f"{kvah_counter:.3f}",
            "instant_kva": f"{random.uniform(50, 200):.3f}",
            "r_voltage": f"{random.uniform(220, 240):.2f}",
            "y_voltage": f"{random.uniform(220, 240):.2f}",
            "b_voltage": f"{random.uniform(220, 240):.2f}",
            "r_current": f"{random.uniform(40, 230):.2f}",
            "y_current": f"{random.uniform(40, 230):.2f}",
            "b_current": f"{random.uniform(40, 230):.2f}",
            "r_pf": "-1.00",
            "y_pf": "-1.00",
            "b_pf": "-1.00",
            "cumulative_pf": "0.99",
            "frequency": "50.00",
            "signal_strength": str(random.randint(20, 35)),
            "md_kva": "0.000",
            "md_time": None,
            "meter_timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "meter_rtc": None
        }

        # Add to current day's data
        current_day_data.append(latest_data.copy())

@app.on_event("startup")
async def start_background():
    asyncio.create_task(generate_data_forever())

@app.on_event("shutdown")
def shutdown_db_client():
    client.close()

@app.get("/live-meter-data")
async def get_latest_data():
    """Returns the latest meter reading"""
    return latest_data

@app.get("/today-data")
async def get_today_data():
    """Returns all readings from the current day"""
    return {
        "date": current_day.strftime("%Y-%m-%d"),
        "readings": current_day_data,
        "count": len(current_day_data)
    }

@app.get("/historical-data/{date}")
async def get_historical_data(date: str):
    """Retrieves stored data for a specific date (YYYY-MM-DD format)"""
    try:
        data = collection.find_one({"date": date}, {"_id": 0})
        return data if data else {"message": "No data found for this date"}
    except Exception as e:
        return {"error": str(e)}