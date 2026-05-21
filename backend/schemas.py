"""
schemas.py - Pydantic Schemas สำหรับ Request/Response Validation
=================================================================

ไฟล์นี้กำหนด Pydantic models (schemas) สำหรับ:
1. Validate ข้อมูลที่รับเข้ามาจาก API request (Request Body)
2. กำหนดโครงสร้าง response ที่ส่งกลับ (Response Body)
3. สร้าง API documentation อัตโนมัติ (Swagger / ReDoc)

Naming Convention:
- XxxCreate  → Schema สำหรับสร้างข้อมูลใหม่ (POST)
- XxxUpdate  → Schema สำหรับอัพเดทข้อมูล (PUT/PATCH)
- XxxOut     → Schema สำหรับ response (GET)

Design Note:
- แยก schemas ออกจาก models เพื่อ:
  1. ไม่ expose ข้อมูลที่ไม่ควรส่งกลับ (เช่น hashed_password)
  2. validate ข้อมูล input แยกจาก database schema
  3. รองรับ versioning ของ API ในอนาคต
"""

import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field, EmailStr

from models import (
    GenderEnum, GoalEnum, MealTypeEnum,
    MealGradeEnum, ActivityTypeEnum
)


# ===========================================================================
# User Schemas
# ===========================================================================

class UserCreate(BaseModel):
    """Schema สำหรับสร้างผู้ใช้ใหม่ (POST /users)"""
    username: str = Field(
        ..., min_length=3, max_length=50,
        description="ชื่อผู้ใช้ (3-50 ตัวอักษร)",
        examples=["somchai_dev"]
    )
    email: EmailStr = Field(
        ...,
        description="อีเมลที่ถูกต้อง",
        examples=["somchai@example.com"]
    )
    password: str = Field(
        ..., min_length=8,
        description="รหัสผ่าน (อย่างน้อย 8 ตัวอักษร)"
    )
    weight_kg: float = Field(
        ..., gt=0, le=500,
        description="น้ำหนัก (kg) - ต้องมากกว่า 0",
        examples=[75.5]
    )
    height_cm: float = Field(
        ..., gt=0, le=300,
        description="ส่วนสูง (cm) - ต้องมากกว่า 0",
        examples=[175.0]
    )
    age: int = Field(
        ..., gt=0, le=150,
        description="อายุ (ปี)",
        examples=[30]
    )
    gender: GenderEnum = Field(
        ...,
        description="เพศ: male หรือ female",
        examples=["male"]
    )
    goal: GoalEnum = Field(
        default=GoalEnum.MAINTAIN,
        description="เป้าหมาย: lose_weight, maintain, build_muscle"
    )
    activity_level: float = Field(
        default=1.55, ge=1.2, le=1.9,
        description="ระดับกิจกรรม (1.2=นั่งทำงาน, 1.55=ปานกลาง, 1.9=นักกีฬา)"
    )


class UserUpdate(BaseModel):
    """Schema สำหรับอัพเดทข้อมูลผู้ใช้ (PUT /users/{id})
    
    ทุกฟิลด์เป็น Optional - ส่งเฉพาะที่ต้องการอัพเดท
    """
    weight_kg: Optional[float] = Field(None, gt=0, le=500)
    height_cm: Optional[float] = Field(None, gt=0, le=300)
    age: Optional[int] = Field(None, gt=0, le=150)
    goal: Optional[GoalEnum] = None
    activity_level: Optional[float] = Field(None, ge=1.2, le=1.9)


class UserOut(BaseModel):
    """Schema สำหรับ response ข้อมูลผู้ใช้
    
    Note: ไม่รวม hashed_password เพื่อความปลอดภัย
    """
    id: uuid.UUID
    username: str
    email: str
    weight_kg: float
    height_cm: float
    age: int
    gender: GenderEnum
    goal: GoalEnum
    activity_level: float
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # อนุญาตให้สร้างจาก SQLAlchemy model object


class BMROut(BaseModel):
    """Schema สำหรับผลคำนวณ BMR/TDEE/Daily Budget
    
    แสดงทุก step ของการคำนวณเพื่อความโปร่งใส
    """
    bmr: float = Field(..., description="Basal Metabolic Rate (kcal)")
    tdee: float = Field(..., description="Total Daily Energy Expenditure (kcal)")
    daily_calorie_budget: float = Field(
        ..., description="แคลอรี่ที่ควรทานต่อวัน (ปรับตาม goal)"
    )
    meal_quotas: dict = Field(
        ...,
        description="โควต้าแคลอรี่แยกตามมื้อ",
        examples=[{
            "breakfast": 600,
            "lunch": 800,
            "dinner": 600
        }]
    )


# ===========================================================================
# Meal Schemas
# ===========================================================================

class MealCreate(BaseModel):
    """Schema สำหรับบันทึกมื้ออาหาร (POST /meals)
    
    Note: image จะถูกส่งเป็น multipart/form-data แยกจาก JSON body
    ดังนั้นไม่รวม image field ใน schema นี้
    """
    meal_type: MealTypeEnum = Field(
        ...,
        description="ประเภทมื้อ: breakfast, lunch, dinner, snack"
    )
    meal_date: Optional[date] = Field(
        default=None,
        description="วันที่ (default: วันนี้)"
    )


class MealOut(BaseModel):
    """Schema สำหรับ response ข้อมูลมื้ออาหาร
    
    รวมผลวิเคราะห์จาก AI และเกรดการประเมิน
    """
    id: uuid.UUID
    user_id: uuid.UUID
    meal_type: MealTypeEnum
    meal_date: date
    image_url: Optional[str] = None
    food_name: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    grade: Optional[MealGradeEnum] = None
    quota_calories: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AIFoodAnalysis(BaseModel):
    """Schema สำหรับผลวิเคราะห์อาหารจาก Gemini Vision API
    
    โครงสร้างนี้ match กับ JSON ที่เราขอให้ AI ส่งกลับ
    """
    food_name: str = Field(..., description="ชื่ออาหารที่ตรวจจับได้")
    calories: float = Field(..., ge=0, description="แคลอรี่โดยประมาณ (kcal)")
    protein_g: float = Field(..., ge=0, description="โปรตีน (กรัม)")
    carbs_g: float = Field(..., ge=0, description="คาร์โบไฮเดรต (กรัม)")
    fat_g: float = Field(..., ge=0, description="ไขมัน (กรัม)")


class DailySummaryOut(BaseModel):
    """Schema สำหรับสรุปมื้ออาหารรายวัน"""
    date: date
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    daily_budget: float
    remaining_calories: float
    meals: List[MealOut]


# ===========================================================================
# Activity Schemas
# ===========================================================================

class ActivityCreate(BaseModel):
    """Schema สำหรับบันทึกกิจกรรม (POST /activities)"""
    activity_type: ActivityTypeEnum = Field(
        ...,
        description="ประเภทกิจกรรม"
    )
    activity_date: Optional[date] = Field(
        default=None,
        description="วันที่ (default: วันนี้)"
    )
    duration_minutes: int = Field(
        ..., gt=0,
        description="ระยะเวลา (นาที)",
        examples=[30]
    )
    distance_km: Optional[float] = Field(
        None, ge=0,
        description="ระยะทาง (km) - ถ้ามี"
    )
    notes: Optional[str] = Field(
        None, max_length=500,
        description="บันทึกเพิ่มเติม"
    )


class ActivityOut(BaseModel):
    """Schema สำหรับ response ข้อมูลกิจกรรม"""
    id: uuid.UUID
    user_id: uuid.UUID
    activity_type: ActivityTypeEnum
    activity_date: date
    duration_minutes: int
    distance_km: Optional[float] = None
    calories_burned: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===========================================================================
# WeeklyGoal Schemas
# ===========================================================================

class WeeklyGoalCreate(BaseModel):
    """Schema สำหรับตั้งเป้าหมายรายสัปดาห์ (POST /weekly-goals)"""
    activity_type: ActivityTypeEnum = Field(
        ...,
        description="ประเภทกิจกรรมที่ตั้งเป้า"
    )
    target_value: float = Field(
        ..., gt=0,
        description="ค่าเป้าหมาย",
        examples=[30.0]
    )
    target_unit: str = Field(
        default="minutes",
        description="หน่วย: 'km', 'minutes', 'sessions', 'calories'",
        examples=["km"]
    )
    week_start_date: Optional[date] = Field(
        default=None,
        description="วันเริ่มต้นสัปดาห์ (default: วันจันทร์ของสัปดาห์ปัจจุบัน)"
    )


class WeeklyGoalOut(BaseModel):
    """Schema สำหรับ response เป้าหมายรายสัปดาห์"""
    id: uuid.UUID
    user_id: uuid.UUID
    activity_type: ActivityTypeEnum
    target_value: float
    target_unit: str
    current_value: float
    is_completed: bool
    week_start_date: date
    week_end_date: date
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WeeklyProgressOut(BaseModel):
    """Schema สำหรับ response ความคืบหน้า + คำแนะนำ
    
    รวมผลคำนวณ dynamic recommendation ด้วย
    """
    goal: WeeklyGoalOut
    remaining_value: float = Field(
        ..., description="ค่าที่เหลือต้องทำ"
    )
    days_remaining: int = Field(
        ..., description="จำนวนวันที่เหลือในสัปดาห์"
    )
    daily_recommendation: float = Field(
        ..., description="ค่าที่แนะนำให้ทำต่อวัน"
    )
    progress_percentage: float = Field(
        ..., description="เปอร์เซ็นต์ความคืบหน้า"
    )
    message: str = Field(
        ..., description="ข้อความแนะนำ (ภาษาไทย)"
    )
