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

# โหลดข้อมูลจากไฟล์ JSON
def load_data():
    try:
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

# บันทึกข้อมูลลงไฟล์ JSON
def save_data(data):
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=2)

# ตรวจสอบความถูกต้องของ ip_address
def validate_ip_address(ip_address):
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False

# ตรวจสอบความถูกต้องของ datetime
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
    
    # เพิ่ม - ลบ จำนวนทั้งเข้าและออกตรงนี้
    total_enter: int
    total_exit: int
    if latest_data:
        total_enter = latest_data["total_enter"] + 1
        total_exit = latest_data["total_exit"] + 1
    else:
        total_enter = 1
        total_exit = 1
    
    # สร้าง transaction ใหม่
    new_transaction = {
        "ip_address": ip_address,
        "last_timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
        "total_enter": total_enter,
        "total_exit": total_exit,
        "start_time": start_time,
        "end_time": end_time
    }
    db_data.append(new_transaction)

    # บันทึกข้อมูลล่าสุด
    save_data(db_data)

    # return JSONResponse
    return JSONResponse(content={
        "success": True, 
        "total_enter": new_transaction["total_enter"], 
        "total_exit": new_transaction["total_exit"]
    })