"""
main.py - FastAPI Application Entry Point
==========================================

ไฟล์หลักของ Backend API สำหรับ Self-Development Web Application

Architecture Overview:
├── /users           → จัดการข้อมูลผู้ใช้ + คำนวณ BMR/TDEE
├── /meals           → บันทึกมื้ออาหาร + วิเคราะห์ด้วย AI (Gemini Vision)
├── /activities      → บันทึกกิจกรรมออกกำลังกาย
└── /weekly-goals    → จัดการเป้าหมายรายสัปดาห์ + คำแนะนำอัจฉริยะ

การรัน:
    uvicorn main:app --reload --port 8000

API Documentation:
    - Swagger UI:  http://localhost:8000/docs
    - ReDoc:       http://localhost:8000/redoc
"""

import os
import json
import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from pathlib import Path

from database import engine, get_db, Base
from models import (
    User, Meal, Activity, WeeklyGoal,
    GenderEnum, GoalEnum, MealTypeEnum,
    MealGradeEnum, ActivityTypeEnum
)
from schemas import (
    UserCreate, UserUpdate, UserOut, BMROut,
    MealCreate, MealOut, AIFoodAnalysis, DailySummaryOut,
    ActivityCreate, ActivityOut,
    WeeklyGoalCreate, WeeklyGoalOut, WeeklyProgressOut
)


# ===========================================================================
# Application Initialization
# ===========================================================================

# สร้าง FastAPI instance พร้อม metadata สำหรับ API docs
app = FastAPI(
    title="Self-Development API",
    description="""
    🏋️ **Self-Development Web Application API**
    
    ระบบจัดการเป้าหมายและสุขภาพส่วนบุคคล ประกอบด้วย:
    
    - **Food AI Vision**: วิเคราะห์อาหารจากรูปภาพด้วย Gemini Vision
    - **Activity Tracker**: ติดตามกิจกรรมและเป้าหมายรายสัปดาห์
    - **BMR Calculator**: คำนวณแคลอรี่ที่ร่างกายต้องการ
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ---------------------------------------------------------------------------
# CORS Middleware Configuration
# ---------------------------------------------------------------------------
# อนุญาตให้ Frontend (Vue.js) เรียก API ข้าม origin ได้
# ใน production ควรจำกัด origins ให้เฉพาะ domain ที่อนุญาต
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev server (Vue.js default)
        "http://localhost:3000",    # Alternative dev port
        "http://localhost:8080",    # Vue CLI default
    ],
    allow_credentials=True,
    allow_methods=["*"],            # อนุญาตทุก HTTP method (GET, POST, PUT, DELETE)
    allow_headers=["*"],            # อนุญาตทุก header (Authorization, Content-Type, etc.)
)


# ---------------------------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------------------------
# สร้างตารางทั้งหมดจาก models เมื่อ application เริ่มทำงาน
# หมายเหตุ: ใน production ควรใช้ Alembic migration แทน
Base.metadata.create_all(bind=engine)


# ===========================================================================
# Utility Functions - ฟังก์ชันช่วยคำนวณ
# ===========================================================================

# ค่าโควต้าแคลอรี่ตามมื้อ (เป็นสัดส่วนของ Daily Budget)
MEAL_QUOTA_PERCENTAGES = {
    MealTypeEnum.BREAKFAST: 0.30,   # มื้อเช้า 30%
    MealTypeEnum.LUNCH: 0.40,       # มื้อกลางวัน 40%
    MealTypeEnum.DINNER: 0.30,      # มื้อเย็น 30%
    MealTypeEnum.SNACK: 0.0,        # ของว่าง (ไม่มีโควต้าแยก)
}

# ค่า MET (Metabolic Equivalent of Task) สำหรับแต่ละกิจกรรม
# ใช้คำนวณ: calories_burned = MET × weight_kg × (duration_minutes / 60)
MET_VALUES = {
    ActivityTypeEnum.RUNNING: 9.8,
    ActivityTypeEnum.WALKING: 3.5,
    ActivityTypeEnum.CYCLING: 7.5,
    ActivityTypeEnum.SWIMMING: 8.0,
    ActivityTypeEnum.WEIGHT_TRAINING: 6.0,
    ActivityTypeEnum.YOGA: 3.0,
    ActivityTypeEnum.OTHER: 4.0,
}

# ค่า multiplier สำหรับปรับ Daily Budget ตามเป้าหมาย
GOAL_MULTIPLIERS = {
    GoalEnum.LOSE_WEIGHT: 0.80,     # ขาดดุล 20%
    GoalEnum.MAINTAIN: 1.00,        # รักษาระดับ
    GoalEnum.BUILD_MUSCLE: 1.15,    # เกินดุล 15%
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: GenderEnum) -> float:
    """
    คำนวณ BMR ด้วยสมการ Mifflin-St Jeor
    
    สมการ:
        BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + constant
        - constant = +5  สำหรับผู้ชาย
        - constant = -161 สำหรับผู้หญิง
    
    Args:
        weight_kg: น้ำหนักเป็น kg
        height_cm: ส่วนสูงเป็น cm
        age: อายุเป็นปี
        gender: เพศ (male/female)
    
    Returns:
        BMR ในหน่วย kcal/day
    
    Example:
        >>> calculate_bmr(80, 175, 30, GenderEnum.MALE)
        1748.75
    """
    constant = 5 if gender == GenderEnum.MALE else -161
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + constant
    return round(bmr, 2)


def calculate_daily_budget(bmr: float, activity_level: float, goal: GoalEnum) -> float:
    """
    คำนวณ Daily Calorie Budget
    
    ขั้นตอน:
    1. TDEE = BMR × activity_level
    2. Daily Budget = TDEE × goal_multiplier
    
    Args:
        bmr: Basal Metabolic Rate
        activity_level: ระดับกิจกรรม (1.2-1.9)
        goal: เป้าหมาย (ลดน้ำหนัก/รักษา/สร้างกล้ามเนื้อ)
    
    Returns:
        Daily Calorie Budget ในหน่วย kcal/day
    """
    tdee = bmr * activity_level
    multiplier = GOAL_MULTIPLIERS.get(goal, 1.0)
    return round(tdee * multiplier, 2)


def grade_meal(actual_calories: float, quota_calories: float) -> MealGradeEnum:
    """
    ประเมินเกรดมื้ออาหาร โดยเทียบแคลอรี่จริงกับโควต้า
    
    เกณฑ์:
    - Good:   actual <= quota × 1.10 (ไม่เกิน 10%)
    - Medium: actual <= quota × 1.30 (เกิน 10-30%)
    - Bad:    actual >  quota × 1.30 (เกิน 30%+)
    
    Args:
        actual_calories: แคลอรี่ที่ทานจริง
        quota_calories: โควต้าแคลอรี่ของมื้อนั้น
    
    Returns:
        MealGradeEnum: good, medium, หรือ bad
    """
    if quota_calories <= 0:
        return MealGradeEnum.MEDIUM

    ratio = actual_calories / quota_calories
    
    if ratio <= 1.10:
        return MealGradeEnum.GOOD
    elif ratio <= 1.30:
        return MealGradeEnum.MEDIUM
    else:
        return MealGradeEnum.BAD


def get_week_boundaries(reference_date: date = None) -> tuple[date, date]:
    """
    คำนวณวันจันทร์และวันอาทิตย์ของสัปดาห์ที่กำหนด
    
    Args:
        reference_date: วันที่อ้างอิง (default: วันนี้)
    
    Returns:
        tuple: (monday, sunday) ของสัปดาห์นั้น
    """
    if reference_date is None:
        reference_date = date.today()
    
    # หาวันจันทร์ (weekday 0 = Monday)
    monday = reference_date - timedelta(days=reference_date.weekday())
    sunday = monday + timedelta(days=6)
    
    return monday, sunday


def calculate_calories_burned(
    activity_type: ActivityTypeEnum,
    duration_minutes: int,
    weight_kg: float
) -> float:
    """
    คำนวณแคลอรี่ที่เผาผลาญจากกิจกรรม
    
    สูตร: calories = MET × weight_kg × (duration_minutes / 60)
    
    Args:
        activity_type: ประเภทกิจกรรม
        duration_minutes: ระยะเวลา (นาที)
        weight_kg: น้ำหนักผู้ใช้ (kg)
    
    Returns:
        แคลอรี่ที่เผาผลาญ (kcal)
    """
    met = MET_VALUES.get(activity_type, 4.0)
    duration_hours = duration_minutes / 60
    return round(met * weight_kg * duration_hours, 2)


# ===========================================================================
# AI Service - Gemini Vision Integration (Placeholder)
# ===========================================================================

async def analyze_food_image(image_bytes: bytes) -> AIFoodAnalysis:
    """
    วิเคราะห์รูปภาพอาหารด้วย Google Gemini Vision API
    
    Flow:
    1. รับ image bytes จาก uploaded file
    2. ส่งไปยัง Gemini Vision API พร้อม prompt ที่กำหนด
    3. Parse response เป็น AIFoodAnalysis schema
    
    Prompt ที่ส่งให้ AI:
    "Analyze this food image and return JSON with:
     food_name, calories, protein_g, carbs_g, fat_g"
    
    TODO: ใส่ GOOGLE_API_KEY จาก environment variable
    
    Args:
        image_bytes: raw bytes ของรูปภาพ
    
    Returns:
        AIFoodAnalysis: ผลวิเคราะห์สารอาหาร
    
    Raises:
        HTTPException: ถ้า AI ไม่สามารถวิเคราะห์ได้
    """
    # ------------------------------------------------------------------
    # TODO: เปิดใช้งานเมื่อมี API key
    # ------------------------------------------------------------------
    # import google.generativeai as genai
    #
    # genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    # model = genai.GenerativeModel("gemini-1.5-flash")
    #
    # prompt = """
    # วิเคราะห์รูปอาหารนี้ และตอบกลับเป็น JSON format เท่านั้น:
    # {
    #     "food_name": "ชื่ออาหาร (ภาษาไทย)",
    #     "calories": ตัวเลข (kcal โดยประมาณ),
    #     "protein_g": ตัวเลข (กรัม),
    #     "carbs_g": ตัวเลข (กรัม),
    #     "fat_g": ตัวเลข (กรัม)
    # }
    # ห้ามตอบอย่างอื่นนอกจาก JSON
    # """
    #
    # import PIL.Image
    # import io
    # image = PIL.Image.open(io.BytesIO(image_bytes))
    # response = model.generate_content([prompt, image])
    # result = json.loads(response.text)
    # return AIFoodAnalysis(**result)
    # ------------------------------------------------------------------
    
    # Placeholder response สำหรับ development/testing
    # จะถูกแทนที่ด้วย Gemini Vision API จริงในขั้นตอนถัดไป
    return AIFoodAnalysis(
        food_name="ข้าวผัดกุ้ง (Placeholder)",
        calories=450.0,
        protein_g=15.0,
        carbs_g=55.0,
        fat_g=18.0
    )


# ===========================================================================
# Health Check Endpoint
# ===========================================================================

@app.get(
    "/",
    tags=["Health"],
    summary="Health Check",
    description="ตรวจสอบสถานะของ API server"
)
async def root():
    """
    Health Check - ใช้ตรวจสอบว่า API ทำงานปกติ
    
    Returns:
        dict: สถานะ server + เวลาปัจจุบัน
    """
    return {
        "status": "healthy",
        "message": "Self-Development API is running 🚀",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# ===========================================================================
# API Routes: Users (ผู้ใช้งาน)
# ===========================================================================

@app.post(
    "/users",
    response_model=UserOut,
    status_code=201,
    tags=["Users"],
    summary="สร้างผู้ใช้ใหม่",
    description="ลงทะเบียนผู้ใช้ใหม่พร้อมข้อมูลร่างกายสำหรับคำนวณ BMR"
)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    สร้างผู้ใช้ใหม่ในระบบ
    
    Business Logic:
    1. ตรวจสอบว่า username และ email ไม่ซ้ำ
    2. Hash password (TODO: ใช้ bcrypt ใน production)
    3. สร้าง user record ใน database
    
    Args:
        user_data: ข้อมูลผู้ใช้ (username, email, password, body metrics)
        db: Database session (injected by FastAPI)
    
    Returns:
        UserOut: ข้อมูลผู้ใช้ที่สร้างแล้ว (ไม่รวม password)
    
    Raises:
        409 Conflict: ถ้า username หรือ email ซ้ำ
    """
    # --- ตรวจสอบ username ซ้ำ ---
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=f"Username '{user_data.username}' ถูกใช้งานแล้ว"
        )
    
    # --- ตรวจสอบ email ซ้ำ ---
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=409,
            detail=f"Email '{user_data.email}' ถูกใช้งานแล้ว"
        )
    
    # --- สร้าง User object ---
    # TODO: ใช้ passlib.hash.bcrypt.hash() สำหรับ hash password จริง
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=f"hashed_{user_data.password}",  # Placeholder hash
        weight_kg=user_data.weight_kg,
        height_cm=user_data.height_cm,
        age=user_data.age,
        gender=user_data.gender,
        goal=user_data.goal,
        activity_level=user_data.activity_level
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)   # ดึง generated fields (id, created_at) กลับมา
    
    return new_user


@app.get(
    "/users/{user_id}",
    response_model=UserOut,
    tags=["Users"],
    summary="ดึงข้อมูลผู้ใช้",
    description="ดึงข้อมูลผู้ใช้ตาม ID"
)
async def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    ดึงข้อมูลผู้ใช้ตาม UUID
    
    Args:
        user_id: UUID ของผู้ใช้
        db: Database session
    
    Returns:
        UserOut: ข้อมูลผู้ใช้
    
    Raises:
        404 Not Found: ถ้าไม่พบผู้ใช้
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    return user


@app.put(
    "/users/{user_id}",
    response_model=UserOut,
    tags=["Users"],
    summary="อัพเดทข้อมูลผู้ใช้",
    description="อัพเดทข้อมูลร่างกายหรือเป้าหมาย"
)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    อัพเดทข้อมูลผู้ใช้ (Partial Update)
    
    รองรับ partial update - ส่งเฉพาะ field ที่ต้องการเปลี่ยน
    
    Args:
        user_id: UUID ของผู้ใช้
        user_data: ข้อมูลที่ต้องการอัพเดท
        db: Database session
    
    Returns:
        UserOut: ข้อมูลผู้ใช้หลังอัพเดท
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    
    # อัพเดทเฉพาะ field ที่ส่งมา (exclude_unset=True ข้าม field ที่ไม่ได้ส่ง)
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


@app.get(
    "/users/{user_id}/bmr",
    response_model=BMROut,
    tags=["Users"],
    summary="คำนวณ BMR/TDEE",
    description="คำนวณ BMR, TDEE, Daily Budget และโควต้ามื้ออาหาร"
)
async def get_user_bmr(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    คำนวณค่าพลังงานทั้งหมดของผู้ใช้
    
    ลำดับการคำนวณ:
    1. BMR = Mifflin-St Jeor equation
    2. TDEE = BMR × activity_level
    3. Daily Budget = TDEE × goal_multiplier
    4. Meal Quotas = Daily Budget × meal_percentages
    
    Example Response:
    {
        "bmr": 1748.75,
        "tdee": 2710.56,
        "daily_calorie_budget": 2168.45,
        "meal_quotas": {
            "breakfast": 650.54,
            "lunch": 867.38,
            "dinner": 650.54
        }
    }
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    
    # --- ขั้นตอนที่ 1: คำนวณ BMR ---
    bmr = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
    
    # --- ขั้นตอนที่ 2: คำนวณ TDEE ---
    tdee = round(bmr * user.activity_level, 2)
    
    # --- ขั้นตอนที่ 3: คำนวณ Daily Budget ---
    daily_budget = calculate_daily_budget(bmr, user.activity_level, user.goal)
    
    # --- ขั้นตอนที่ 4: แบ่งโควต้ามื้ออาหาร ---
    meal_quotas = {
        "breakfast": round(daily_budget * 0.30, 2),
        "lunch": round(daily_budget * 0.40, 2),
        "dinner": round(daily_budget * 0.30, 2),
    }
    
    return BMROut(
        bmr=bmr,
        tdee=tdee,
        daily_calorie_budget=daily_budget,
        meal_quotas=meal_quotas
    )


# ===========================================================================
# API Routes: Meals (มื้ออาหาร + AI Vision)
# ===========================================================================

@app.post(
    "/users/{user_id}/meals",
    response_model=MealOut,
    status_code=201,
    tags=["Meals"],
    summary="บันทึกมื้ออาหาร + วิเคราะห์ AI",
    description="""
    อัพโหลดรูปภาพอาหาร → AI วิเคราะห์สารอาหาร → ประเมินเกรด
    
    Flow: Upload Image → Gemini Vision → Calculate Grade → Save to DB
    """
)
async def create_meal(
    user_id: uuid.UUID,
    meal_type: MealTypeEnum = Form(..., description="ประเภทมื้อ"),
    meal_date: Optional[date] = Form(None, description="วันที่ (default: วันนี้)"),
    image: UploadFile = File(..., description="รูปภาพอาหาร (JPEG/PNG)"),
    db: Session = Depends(get_db)
):
    """
    บันทึกมื้ออาหารพร้อมวิเคราะห์ด้วย AI
    
    Processing Pipeline:
    1. Validate: ตรวจสอบว่า user มีอยู่จริง
    2. Upload:  อ่าน image bytes
    3. AI:      ส่งรูปไป Gemini Vision → ได้ food_name, calories, macros
    4. Grade:   เทียบ calories กับโควต้ามื้อนั้น → good/medium/bad
    5. Save:    บันทึกทุกอย่างลง database
    
    Args:
        user_id: UUID ของผู้ใช้
        meal_type: ประเภทมื้อ (breakfast/lunch/dinner/snack)
        meal_date: วันที่ (optional, default=today)
        image: ไฟล์รูปภาพอาหาร
        db: Database session
    
    Returns:
        MealOut: ข้อมูลมื้ออาหารพร้อมผลวิเคราะห์และเกรด
    """
    # --- Step 1: Validate user ---
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    
    # --- Step 2: อ่าน image ---
    image_bytes = await image.read()
    
    # TODO: อัพโหลดรูปไป cloud storage (S3, GCS) แล้วเก็บ URL
    # ตอนนี้ใช้ filename เป็น placeholder
    image_url = f"/uploads/{user_id}/{image.filename}"
    
    # --- Step 3: AI Analysis ---
    ai_result = await analyze_food_image(image_bytes)
    
    # --- Step 4: Calculate Grade ---
    # คำนวณ daily budget ของ user
    bmr = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
    daily_budget = calculate_daily_budget(bmr, user.activity_level, user.goal)
    
    # คำนวณโควต้าของมื้อนี้
    quota_pct = MEAL_QUOTA_PERCENTAGES.get(meal_type, 0.0)
    quota_calories = round(daily_budget * quota_pct, 2)
    
    # ประเมินเกรด
    meal_grade = grade_meal(ai_result.calories, quota_calories)
    
    # --- Step 5: Save to DB ---
    new_meal = Meal(
        user_id=user_id,
        meal_type=meal_type,
        meal_date=meal_date or date.today(),
        image_url=image_url,
        food_name=ai_result.food_name,
        calories=ai_result.calories,
        protein_g=ai_result.protein_g,
        carbs_g=ai_result.carbs_g,
        fat_g=ai_result.fat_g,
        grade=meal_grade,
        quota_calories=quota_calories,
        ai_raw_response=json.dumps(ai_result.model_dump(), ensure_ascii=False)
    )
    
    db.add(new_meal)
    db.commit()
    db.refresh(new_meal)
    
    return new_meal


@app.get(
    "/users/{user_id}/meals",
    response_model=List[MealOut],
    tags=["Meals"],
    summary="ดึงรายการมื้ออาหาร",
    description="ดึงมื้ออาหารของผู้ใช้ ฟิลเตอร์ตามวันที่ได้"
)
async def get_meals(
    user_id: uuid.UUID,
    meal_date: Optional[date] = Query(None, description="ฟิลเตอร์ตามวันที่"),
    db: Session = Depends(get_db)
):
    """
    ดึงรายการมื้ออาหารของผู้ใช้
    
    สามารถฟิลเตอร์ตามวันที่ได้ ถ้าไม่ระบุจะดึงทั้งหมด
    เรียงตามวันที่ล่าสุดก่อน (descending)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    
    query = db.query(Meal).filter(Meal.user_id == user_id)
    
    if meal_date:
        query = query.filter(Meal.meal_date == meal_date)
    
    meals = query.order_by(Meal.meal_date.desc(), Meal.created_at.desc()).all()
    return meals


@app.get(
    "/users/{user_id}/meals/daily-summary",
    response_model=DailySummaryOut,
    tags=["Meals"],
    summary="สรุปมื้ออาหารรายวัน",
    description="รวมแคลอรี่และสารอาหารทั้งวัน เทียบกับ daily budget"
)
async def get_daily_summary(
    user_id: uuid.UUID,
    target_date: date = Query(default=None, description="วันที่ (default: วันนี้)"),
    db: Session = Depends(get_db)
):
    """
    สรุปข้อมูลโภชนาการรายวัน
    
    รวม:
    - แคลอรี่ทั้งหมดที่ทานในวันนั้น
    - สารอาหารรวม (โปรตีน, คาร์บ, ไขมัน)
    - เปรียบเทียบกับ daily budget
    - แคลอรี่ที่เหลือ (remaining)
    """
    if target_date is None:
        target_date = date.today()
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    
    # ดึงมื้ออาหารทั้งหมดของวันนั้น
    meals = db.query(Meal).filter(
        Meal.user_id == user_id,
        Meal.meal_date == target_date
    ).all()
    
    # รวมสารอาหาร
    total_cal = sum(m.calories or 0 for m in meals)
    total_pro = sum(m.protein_g or 0 for m in meals)
    total_carb = sum(m.carbs_g or 0 for m in meals)
    total_fat = sum(m.fat_g or 0 for m in meals)
    
    # คำนวณ daily budget
    bmr = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
    daily_budget = calculate_daily_budget(bmr, user.activity_level, user.goal)
    
    return DailySummaryOut(
        date=target_date,
        total_calories=round(total_cal, 2),
        total_protein_g=round(total_pro, 2),
        total_carbs_g=round(total_carb, 2),
        total_fat_g=round(total_fat, 2),
        daily_budget=daily_budget,
        remaining_calories=round(daily_budget - total_cal, 2),
        meals=meals
    )


# ===========================================================================
# API Routes: Activities (กิจกรรม)
# ===========================================================================

@app.post(
    "/users/{user_id}/activities",
    response_model=ActivityOut,
    status_code=201,
    tags=["Activities"],
    summary="บันทึกกิจกรรม",
    description="บันทึกกิจกรรมออกกำลังกาย พร้อมคำนวณแคลอรี่ที่เผาผลาญ"
)
async def create_activity(
    user_id: uuid.UUID,
    activity_data: ActivityCreate,
    db: Session = Depends(get_db)
):
    """
    บันทึกกิจกรรมออกกำลังกายรายวัน
    
    Processing:
    1. Validate user
    2. คำนวณ calories_burned = MET × weight × (duration/60)
    3. บันทึกลง database
    4. อัพเดท WeeklyGoal ที่เกี่ยวข้อง (ถ้ามี)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    
    # คำนวณแคลอรี่ที่เผาผลาญ
    calories_burned = calculate_calories_burned(
        activity_data.activity_type,
        activity_data.duration_minutes,
        user.weight_kg
    )
    
    new_activity = Activity(
        user_id=user_id,
        activity_type=activity_data.activity_type,
        activity_date=activity_data.activity_date or date.today(),
        duration_minutes=activity_data.duration_minutes,
        distance_km=activity_data.distance_km,
        calories_burned=calories_burned,
        notes=activity_data.notes
    )
    
    db.add(new_activity)
    
    # --- อัพเดท WeeklyGoal ที่เกี่ยวข้อง ---
    activity_date = activity_data.activity_date or date.today()
    monday, sunday = get_week_boundaries(activity_date)
    
    # หา weekly goal ของกิจกรรมประเภทเดียวกันในสัปดาห์นี้
    weekly_goal = db.query(WeeklyGoal).filter(
        WeeklyGoal.user_id == user_id,
        WeeklyGoal.activity_type == activity_data.activity_type,
        WeeklyGoal.week_start_date == monday
    ).first()
    
    if weekly_goal:
        # อัพเดท current_value ตาม unit ของ goal
        if weekly_goal.target_unit == "minutes":
            weekly_goal.current_value += activity_data.duration_minutes
        elif weekly_goal.target_unit == "km" and activity_data.distance_km:
            weekly_goal.current_value += activity_data.distance_km
        elif weekly_goal.target_unit == "calories":
            weekly_goal.current_value += calories_burned
        elif weekly_goal.target_unit == "sessions":
            weekly_goal.current_value += 1
        
        # ตรวจสอบว่าบรรลุเป้าหมายหรือยัง
        if weekly_goal.current_value >= weekly_goal.target_value:
            weekly_goal.is_completed = True
    
    db.commit()
    db.refresh(new_activity)
    
    return new_activity


@app.get(
    "/users/{user_id}/activities",
    response_model=List[ActivityOut],
    tags=["Activities"],
    summary="ดึงรายการกิจกรรม",
    description="ดึงกิจกรรมของผู้ใช้ ฟิลเตอร์ตามวันที่หรือประเภทได้"
)
async def get_activities(
    user_id: uuid.UUID,
    activity_date: Optional[date] = Query(None, description="ฟิลเตอร์ตามวันที่"),
    activity_type: Optional[ActivityTypeEnum] = Query(None, description="ฟิลเตอร์ตามประเภท"),
    db: Session = Depends(get_db)
):
    """ดึงรายการกิจกรรม พร้อมตัวเลือกในการฟิลเตอร์"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    
    query = db.query(Activity).filter(Activity.user_id == user_id)
    
    if activity_date:
        query = query.filter(Activity.activity_date == activity_date)
    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)
    
    activities = query.order_by(Activity.activity_date.desc()).all()
    return activities


# ===========================================================================
# API Routes: Weekly Goals (เป้าหมายรายสัปดาห์)
# ===========================================================================

@app.post(
    "/users/{user_id}/weekly-goals",
    response_model=WeeklyGoalOut,
    status_code=201,
    tags=["Weekly Goals"],
    summary="ตั้งเป้าหมายรายสัปดาห์",
    description="สร้างเป้าหมายกิจกรรมสำหรับสัปดาห์นี้"
)
async def create_weekly_goal(
    user_id: uuid.UUID,
    goal_data: WeeklyGoalCreate,
    db: Session = Depends(get_db)
):
    """
    ตั้งเป้าหมายรายสัปดาห์ใหม่
    
    Business Rules:
    - ผู้ใช้สามารถมี 1 goal ต่อ activity_type ต่อสัปดาห์
    - ถ้ามี goal ซ้ำจะ return 409 Conflict
    - week_start_date จะถูกปรับให้เป็นวันจันทร์เสมอ
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    
    # กำหนดช่วงสัปดาห์
    monday, sunday = get_week_boundaries(goal_data.week_start_date)
    
    # ตรวจสอบว่ามี goal ซ้ำหรือไม่
    existing = db.query(WeeklyGoal).filter(
        WeeklyGoal.user_id == user_id,
        WeeklyGoal.activity_type == goal_data.activity_type,
        WeeklyGoal.week_start_date == monday
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"มีเป้าหมาย '{goal_data.activity_type.value}' สำหรับสัปดาห์นี้แล้ว"
        )
    
    new_goal = WeeklyGoal(
        user_id=user_id,
        activity_type=goal_data.activity_type,
        target_value=goal_data.target_value,
        target_unit=goal_data.target_unit,
        week_start_date=monday,
        week_end_date=sunday,
        current_value=0.0,
        is_completed=False
    )
    
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    
    return new_goal


@app.get(
    "/users/{user_id}/weekly-goals",
    response_model=List[WeeklyGoalOut],
    tags=["Weekly Goals"],
    summary="ดึงเป้าหมายรายสัปดาห์",
    description="ดึงเป้าหมายทั้งหมดของสัปดาห์ที่กำหนด"
)
async def get_weekly_goals(
    user_id: uuid.UUID,
    week_start: Optional[date] = Query(None, description="วันเริ่มต้นสัปดาห์"),
    db: Session = Depends(get_db)
):
    """ดึงเป้าหมายรายสัปดาห์ ถ้าไม่ระบุวันจะดึงสัปดาห์ปัจจุบัน"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    
    monday, _ = get_week_boundaries(week_start)
    
    goals = db.query(WeeklyGoal).filter(
        WeeklyGoal.user_id == user_id,
        WeeklyGoal.week_start_date == monday
    ).all()
    
    return goals


@app.get(
    "/users/{user_id}/weekly-goals/{goal_id}/progress",
    response_model=WeeklyProgressOut,
    tags=["Weekly Goals"],
    summary="ดูความคืบหน้า + คำแนะนำ",
    description="""
    แสดงความคืบหน้าของเป้าหมาย พร้อมคำแนะนำอัจฉริยะ
    
    Dynamic Calculation:
    - remaining = target - current
    - days_left = end_date - today
    - recommendation = remaining / days_left
    """
)
async def get_weekly_progress(
    user_id: uuid.UUID,
    goal_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    คำนวณความคืบหน้าและแนะนำกิจกรรมที่ต้องทำต่อวัน
    
    Recommendation Algorithm:
    1. remaining = target_value - current_value
    2. days_left = (week_end_date - today).days + 1
    3. daily_recommendation = remaining / days_left (ถ้ายังไม่ถึงเป้า)
    4. สร้างข้อความแนะนำภาษาไทย
    
    Example:
    - เป้าหมาย: วิ่ง 30 km/สัปดาห์
    - ทำแล้ว: 15 km (50%)
    - เหลือ: 15 km ใน 4 วัน
    - แนะนำ: "คุณต้องวิ่งวันละ 3.75 km เพื่อให้ทันเป้าหมาย"
    """
    # ดึง goal
    goal = db.query(WeeklyGoal).filter(
        WeeklyGoal.id == goal_id,
        WeeklyGoal.user_id == user_id
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="ไม่พบเป้าหมาย")
    
    # --- Dynamic Calculation ---
    remaining = max(0, goal.target_value - goal.current_value)
    
    today = date.today()
    days_left = max(1, (goal.week_end_date - today).days + 1)
    
    # ถ้ายังไม่ถึงเป้า → คำนวณ recommendation
    if remaining > 0:
        daily_rec = round(remaining / days_left, 2)
    else:
        daily_rec = 0.0
    
    # คำนวณ progress %
    progress_pct = round(
        min(100.0, (goal.current_value / goal.target_value) * 100), 1
    ) if goal.target_value > 0 else 0.0
    
    # --- สร้างข้อความแนะนำ ---
    if goal.is_completed:
        message = f"🎉 ยินดีด้วย! คุณบรรลุเป้าหมาย {goal.activity_type.value} แล้ว!"
    elif progress_pct >= 80:
        message = (
            f"💪 เกือบถึงแล้ว! เหลืออีก {remaining:.1f} {goal.target_unit} "
            f"ใน {days_left} วัน (แนะนำวันละ {daily_rec:.1f} {goal.target_unit})"
        )
    elif progress_pct >= 50:
        message = (
            f"👍 กำลังไปได้ดี! ทำแล้ว {progress_pct:.0f}% "
            f"เหลือ {remaining:.1f} {goal.target_unit} "
            f"(แนะนำวันละ {daily_rec:.1f} {goal.target_unit})"
        )
    else:
        message = (
            f"⚡ มาเร่งกันเถอะ! เหลืออีก {remaining:.1f} {goal.target_unit} "
            f"ใน {days_left} วัน (ต้องทำวันละ {daily_rec:.1f} {goal.target_unit})"
        )
    
    return WeeklyProgressOut(
        goal=goal,
        remaining_value=remaining,
        days_remaining=days_left,
        daily_recommendation=daily_rec,
        progress_percentage=progress_pct,
        message=message
    )


# ===========================================================================
# Static Files - Serve Vue.js Frontend
# ===========================================================================
# เมื่อ build Vue.js แล้ว ไฟล์จะอยู่ใน ../frontend/dist/
# FastAPI จะ serve ไฟล์เหล่านี้เป็น static files
# ทำให้ deploy เป็น app เดียว (Backend + Frontend รวมกัน)

STATIC_DIR = Path(__file__).parent.parent / "frontend" / "dist"

# Mount static assets (JS, CSS, images) ถ้าโฟลเดอร์มีอยู่
if STATIC_DIR.exists():
    # Mount /assets สำหรับ Vite bundled files
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


# Catch-all route: ส่ง index.html สำหรับทุก path ที่ไม่ใช่ API
# ทำให้ Vue Router (client-side routing) ทำงานได้ถูกต้อง
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(request: Request, full_path: str):
    """
    Serve Vue.js SPA - ส่ง index.html สำหรับทุก non-API route
    
    ทำไมต้องมี catch-all route?
    - Vue Router ใช้ client-side routing (เช่น /dashboard, /food)
    - ถ้า user refresh หน้า /dashboard โดยตรง
      server ต้องส่ง index.html กลับไปเพื่อให้ Vue Router จัดการ
    """
    if not STATIC_DIR.exists():
        return {"message": "Frontend not built yet. Run: cd frontend && npm run build"}
    
    # ลองหาไฟล์ static ก่อน (เช่น favicon.ico, robots.txt)
    static_file = STATIC_DIR / full_path
    if static_file.exists() and static_file.is_file():
        return FileResponse(str(static_file))
    
    # ถ้าไม่ใช่ไฟล์ static → ส่ง index.html (Vue Router จัดการ)
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    
    return {"message": "index.html not found"}


# ===========================================================================
# Application Startup Event
# ===========================================================================

@app.on_event("startup")
async def startup_event():
    """
    Event ที่ทำงานเมื่อ application เริ่มต้น
    """
    print("=" * 60)
    print("🚀 Self-Development API Started!")
    print(f"📖 API Docs:    http://localhost:8000/docs")
    print(f"📖 ReDoc:       http://localhost:8000/redoc")
    if STATIC_DIR.exists():
        print(f"🌐 Frontend:    Serving from {STATIC_DIR}")
    else:
        print(f"⚠️  Frontend:    Not built yet (cd frontend && npm run build)")
    print(f"🕐 Started at:  {datetime.now().isoformat()}")
    print("=" * 60)


# ===========================================================================
# Run with: uvicorn main:app --reload --port 8000
# ===========================================================================
