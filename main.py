import json, fastapi, ipaddress, xmltodict
from pydantic import BaseModel, ValidationError
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import Request

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