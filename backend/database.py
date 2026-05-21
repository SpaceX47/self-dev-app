"""
database.py - การตั้งค่าการเชื่อมต่อฐานข้อมูล (Database Connection Configuration)
=================================================================================

ไฟล์นี้รับผิดชอบการสร้าง Engine, SessionLocal, และ Base class สำหรับ SQLAlchemy ORM
ใช้ pattern "Dependency Injection" ผ่าน get_db() เพื่อให้ FastAPI จัดการ session lifecycle

Architecture Note:
- แยก database config ออกจาก models เพื่อหลีกเลี่ยง circular imports
- ใช้ environment variable สำหรับ connection string เพื่อความปลอดภัย
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Database URL Configuration
# ---------------------------------------------------------------------------
# รูปแบบ: postgresql://username:password@host:port/database_name
# ใช้ os.environ.get() เพื่อดึงค่าจาก environment variable
# ถ้าไม่ได้ตั้ง env var จะใช้ค่า default สำหรับ local development
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/self_dev_db"
)

# ---------------------------------------------------------------------------
# SQLAlchemy Engine
# ---------------------------------------------------------------------------
# Engine เป็นจุดเชื่อมต่อหลักระหว่าง Python กับ PostgreSQL
# - pool_pre_ping=True: ตรวจสอบว่า connection ยังใช้งานได้ก่อนใช้งาน
#   ป้องกัน "stale connection" error เมื่อ DB restart
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # ตั้งเป็น True เพื่อ debug SQL queries ใน console
)

# ---------------------------------------------------------------------------
# Session Factory
# ---------------------------------------------------------------------------
# SessionLocal เป็น factory function สำหรับสร้าง database session
# - autocommit=False: ต้อง commit() เอง เพื่อควบคุม transaction อย่างชัดเจน
# - autoflush=False: ป้องกันการ flush อัตโนมัติ ให้ควบคุมเองเมื่อพร้อม
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------
# Base class ที่ทุก model จะ inherit ไป
# SQLAlchemy ใช้ Base นี้ในการ track metadata ของทุกตาราง
Base = declarative_base()


# ---------------------------------------------------------------------------
# Dependency: get_db()
# ---------------------------------------------------------------------------
# Generator function สำหรับใช้เป็น FastAPI Dependency
# Pattern: "Session per Request"
# - สร้าง session ใหม่ทุกครั้งที่มี API request เข้ามา
# - yield session ให้ route handler ใช้งาน
# - finally block รับประกันว่า session จะถูกปิดเสมอ แม้เกิด error
def get_db():
    """
    Dependency function สำหรับ FastAPI
    
    Usage ใน route handler:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
