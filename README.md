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
โมดูล xmltodict เป็นโมดูลสำหรับช่วยให้สามารถทำงานกับ XML ได้สะดวกยิ่งขึ้น
สามารถติดตั้งได้โดยใช้คำสั่ง pip:
```
pip install xmltodict
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
import json, fastapi, ipaddress, xmltodict
from pydantic import BaseModel, ValidationError
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import Request

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
    
# ตรวจสอบ element ต่างๆ ใน XML
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

        # ตรวจสอบหา ip address ที่ไม่มีในฐานข้อมูล
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
ทำการทดสอบโดยการ POST call มาที่ http://127.0.0.1:8000/count_people และตั้งค่า body เป็นรูปแบบ XML
```
<EventNotificationAlert version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema"> <ipAddress>192.168.2.64</ipAddress>
<portNo>8080</portNo>
<protocol>HTTP</protocol>
<macAddress>3c:1b:f8:c1:3a:6d</macAddress>
<channelID>1</channelID>
<dateTime>2024-07-08T12:27:24+08:00</dateTime> <activePostCount>1</activePostCount>
<eventType>PeopleCounting</eventType>
<eventState>active</eventState>
<eventDescription>PeopleCounting alarm</eventDescription> <channelName>Camera 01</channelName>
<peopleCounting>
<statisticalMethods>realTime</statisticalMethods>
<RealTime>
<time>2024-07-08T12:27:24+08:00</time>
</RealTime>
<enter>15</enter>
<exit>14</exit>
<duplicatePeople>4</duplicatePeople> <countingSceneMode>entrance</countingSceneMode>
</peopleCounting>
<isDataRetransmission>false</isDataRetransmission>
</EventNotificationAlert>
```
ผลลัพธ์ที่ได้
```
{
    "message": "Data received and saved"
}
```

หลังจาก รับข้อมูล XML Event Notification มาแล้ว ก็สามารถ POST call ตรวจสอบมาที่ http://127.0.0.1:8000/count_people และตั้งค่า body (กรอก ip และช่วงเวลาให้ครอบคลุมข้อมูลที่มี)
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