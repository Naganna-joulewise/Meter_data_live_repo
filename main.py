from fastapi import FastAPI
from datetime import datetime, timedelta
import random
import asyncio

app = FastAPI()

kvah_counter = 637000.0
latest_data = {}

async def generate_data_forever():
    global kvah_counter, latest_data

    while True:
        wait_seconds = random.randint(60, 600)  # 1 to 10 minutes
        await asyncio.sleep(wait_seconds)

        current_time = datetime.utcnow()  # Use UTC (Render server timezone)

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

@app.on_event("startup")
async def start_background():
    asyncio.create_task(generate_data_forever())

@app.get("/live-meter-data")
def get_latest_data():
    return latest_data