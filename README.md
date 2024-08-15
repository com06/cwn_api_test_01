# Python สร้าง API ด้วย FastAPI

FastAPI เป็นอีกหนึ่งเฟรมเวิร์ก Python สำหรับสร้าง API ที่ได้รับความนิยม ด้วยความสามารถในการสร้าง API ที่มีประสิทธิภาพสูง รองรับการทำงานแบบ asynchronous และมาพร้อมกับฟีเจอร์ที่หลากหลาย ทำให้ FastAPI เป็นตัวเลือกที่ยอดเยี่ยม

## Install FastAPI
อย่างแรกก็ต้องติดตั้ง FastAPI ด้วยคำสั่งด้านล่างนี้

```
pip intsall fastapi
```
ต่อมาก็ ติดตั้ง Uvicorn อีกหนึ่งตัวที่สำคัญเหมือนกันในการเป็น Server ที่รันไฟล์ python ที่เราสร้างขึ้นมา

```
pip install uvicorn
```

## live server

ทำการรัน  live server ด้วยคำสั่ง 
```
uvicorn main:app --reload
```