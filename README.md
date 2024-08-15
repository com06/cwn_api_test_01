# Python สร้าง API ด้วย FastAPI

FastAPI เป็นอีกหนึ่งเฟรมเวิร์ก Python สำหรับสร้าง API ที่ได้รับความนิยม ด้วยความสามารถในการสร้าง API ที่มีประสิทธิภาพสูง รองรับการทำงานแบบ asynchronous และมาพร้อมกับฟีเจอร์ที่หลากหลาย ทำให้ FastAPI เป็นตัวเลือกที่ยอดเยี่ยม

โดยโค้ดตัวอย่างนี้กล่าวถึงอาคารอัจฉริยะ ที่ติดตั้งกล้อง IP ไว้ที่ทางเข้าต่างๆ เพื่อคอยนับจำนวนคนที่เข้าและออกจากอาคาร

## Install FastAPI
อย่างแรกก็ต้องติดตั้ง FastAPI ด้วยคำสั่งด้านล่างนี้

```
pip intsall fastapi
```
ต่อมาก็ ติดตั้ง Uvicorn อีกหนึ่งตัวที่สำคัญเหมือนกันในการเป็น Server ที่รันไฟล์ python ที่เราสร้างขึ้นมา

```
pip install uvicorn
```

## Live server

ทำการรัน  live server ด้วยคำสั่ง 
```
uvicorn main:app --reload
```

## main.py

ไฟล์ main.py จะประกอบไปด้วย
การนำเข้าไลบรารีที่จำเป็น และ path ของไฟล์ json ที่เราจะนำมาเก็บข้อมูล
```
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
```
ส่วนถัดไปเป็นพวก function ต่างๆ
```
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
```
ส่วนสุดท้ายสร้าง endpoint /count_people
```
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
```
## Document
อีกหนึ่งจุดเด่นของ FastAPI ก็คือมี Interactive API docs ที่นำ Swagger UI เข้ามาจัดการให้ โดยไปที่ http://127.0.0.1:8000/docs

## ทดสอบด้วย Postman
ทำการทดสอบโดยการ POST call มาที่ http://127.0.0.1:8000/count_people และตั้งค่า body
```
{
    "ip_address": "192.168.2.64",
    "start_time": "20240708102000",
    "end_time": "20240708103000"
}
```
ผลลัพธ์ที่ได้
```
{
    "success": true,
    "total_enter": 3,
    "total_exit": 3
}
```
โดยผลลัพธ์จะ +1 ใส่ total_enter และ total_exit ของ last_timestamp ล่าสุด โดยโค้ดชุดนี้ยังไม่ได้บอกถึงข้อมูลว่าคนที่เดินเข้าตึกมานั้น เป็นคนเดินเข้าหรือเดินออก