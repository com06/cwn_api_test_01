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

def save_to_json(data):
    with open(DB_PATH, 'r') as f:
        try:
            existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = []

    existing_data.append(data)

    with open(DB_PATH, 'w') as f:
        json.dump(existing_data, f, indent=2)

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

def check_required_fields(data):
    required_fields = ['ipAddress', 'macAddress', 'channelID', 'eventType', 'eventState', 'channelName', 'peopleCounting.enter', 'peopleCounting.exit', 'peopleCounting.countingSceneMode']

    # ตรวจสอบ field ระดับบนสุด
    for field in required_fields:
        if '.' not in field:
            if field not in data or data[field] is None:
                return False

    # ตรวจสอบ field ที่อยู่ใน peopleCounting
    for field in required_fields:
        if '.' in field:
            field_parts = field.split('.')
            if field_parts[0] not in data or field_parts[1] not in data[field_parts[0]] or data[field_parts[0]][field_parts[1]] is None:
                return False

    return True
```
ตามด้วย /detect
```
#------- detect -------
@app.post("/detect")
async def detect(request: Request):
    try:
        xml_data = await request.body()
        data = xmltodict.parse(xml_data)['EventNotificationAlert']

        # เช็ค field ใน XML
        if not check_required_fields(data):
            return JSONResponse(status_code=400, content={"message": "Missing required fields"})
        
        # อ่านข้อมูลจากไฟล์ JSON
        db_data = load_data()

        # สร้างข้อมูลที่จะบันทึกโดยตรงจาก data
        new_data = {
            "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
            **data
        }
        db_data.append(new_data)

        # บันทึกข้อมูลล่าสุด
        save_data(db_data)

        return JSONResponse(content={"message": "Data received and saved"})
    except (xmltodict.ParsingError, KeyError) as e:
        return JSONResponse(status_code=400, content={"message": f"Error parsing XML: {str(e)}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Internal Server Error: {str(e)}"})

```
และก็อีกอัน /count_people
```
#------- count_people -------
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
        
        # อ่านข้อมูลจากไฟล์ JSON
        db_data = load_data()

        camera_data = [camera_ip for camera_ip in db_data if camera_ip['ipAddress'] == ip_address]
        if not camera_data:
            raise ValueError("Data not found")

        total_enter = 0
        total_exit = 0
        for event in db_data:
            # สตริงวันที่และเวลาในรูปแบบเดิม
            date_time_str = event['dateTime']

            # แปลงสตริงเป็นวัตถุ datetime
            dt = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S%z")

            # แปลงกลับเป็นสตริงในรูปแบบใหม่
            dateTime_format_str = dt.strftime("%Y%m%d%H%M%S")

            # if event['ipAddress'] == ip_address and start_time <= event_time <= end_time:
            if event['ipAddress'] == ip_address and start_time <= dateTime_format_str <= end_time:
                total_enter += int(event['peopleCounting']['enter'])
                total_exit += int(event['peopleCounting']['exit'])
                
        # total_difference += total_enter - total_exit
        return JSONResponse(content={
            "success": True, 
            "total_enter": total_enter, 
            "total_exit": total_exit
        })

    except ValueError as e:
        return JSONResponse(status_code=400, content={"message": str(e)})
    except ValidationError as e:
        return JSONResponse(status_code=400, content={"message": str(e)})
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