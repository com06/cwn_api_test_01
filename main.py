import json
import fastapi
import ipaddress
from pydantic import BaseModel, ValidationError
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import HTTPException

app = fastapi.FastAPI()

# กำหนด path ของไฟล์ JSON
DB_PATH = "data/db.json"

# Model สำหรับรับข้อมูลจาก request
class PersonCountRequest(BaseModel):
    ip_address: str
    start_time: str
    end_time: str

def load_data():
    try:
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_data(data):
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def validate_ip_address(ip_address):
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False

def validate_datetime(datetime_str, format="%Y%m%d%H%M%S"):
    try:
        datetime.strptime(datetime_str, format)
        return True
    except ValueError:
        return False

@app.post("/count_people")
async def count_people(request: PersonCountRequest):
    ip_address = request.ip_address
    start_time = request.start_time
    end_time = request.end_time

    try:
        # ตรวจสอบรูปแบบ
        if not validate_ip_address(ip_address):
            raise ValueError("Invalid IP address format")
        if not validate_datetime(start_time) or not validate_datetime(end_time):
            raise ValueError("Invalid datetime format")

    except ValueError as e:
        return JSONResponse(status_code=400, content={"message": str(e)})
    except ValidationError as e:
        return JSONResponse(status_code=400, content={"message": str(e)})

    # อ่านข้อมูลจากไฟล์ JSON
    db_data = load_data()

    # หาข้อมูลที่มี last_timestamp มากที่สุด
    latest_data = max(db_data, key=lambda x: x['last_timestamp'], default=None)
    
    # 
    last_count: int
    if latest_data:
        last_count = latest_data["last_count"] + 1
    else:
        last_count = 1
    
    # สร้าง transaction ใหม่
    new_transaction = {
        "ip_address": ip_address,
        "last_timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
        "last_count": last_count,
        "start_time": start_time,
        "end_time": end_time
    }
    db_data.append(new_transaction)

    # บันทึกข้อมูลใหม่
    save_data(db_data)

    # return JSONResponse(content={"total_count": camera_data["last_count"]})
    return JSONResponse(content={
        "success": True, 
        "total_enter": new_transaction["last_count"], 
        "total_exit": new_transaction["last_count"]
    })