"""
models.py - โครงสร้างฐานข้อมูลทั้งหมด (Database Models / Schema Definition)
==============================================================================

ไฟล์นี้กำหนดโครงสร้างตาราง (Table Schema) ทั้ง 4 ตาราง ด้วย SQLAlchemy ORM:

1. User       - ข้อมูลผู้ใช้งาน (น้ำหนัก, ส่วนสูง, อายุ, เพศ, เป้าหมาย)
2. Meal       - บันทึกมื้ออาหาร (ภาพอาหาร, แคลอรี่, สารอาหาร, เกรด)
3. Activity   - บันทึกกิจกรรมรายวัน (ประเภท, ระยะเวลา, แคลอรี่ที่เผาผลาญ)
4. WeeklyGoal - เป้าหมายรายสัปดาห์ (เป้าหมาย, ความคืบหน้า)

Relationships (ความสัมพันธ์):
- User 1:N Meal       (ผู้ใช้ 1 คน มีหลายมื้ออาหาร)
- User 1:N Activity   (ผู้ใช้ 1 คน มีหลายกิจกรรม)
- User 1:N WeeklyGoal (ผู้ใช้ 1 คน มีหลายเป้าหมายรายสัปดาห์)

Design Decisions:
- ใช้ UUID เป็น primary key แทน auto-increment integer เพื่อความปลอดภัย
  และรองรับ distributed systems ในอนาคต
- ทุกตารางมี created_at/updated_at สำหรับ audit trail
- ใช้ Enum สำหรับฟิลด์ที่มีค่าจำกัด (เพศ, ประเภทมื้ออาหาร, เกรด, เป้าหมาย)
"""

import uuid
from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Float, Date, DateTime,
    ForeignKey, Text, Enum as SAEnum, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# ===========================================================================
# Enum Definitions - ค่าคงที่ที่ใช้ในระบบ
# ===========================================================================

class GenderEnum(str, PyEnum):
    """เพศของผู้ใช้ - ใช้ในการคำนวณ BMR
    
    สมการ Mifflin-St Jeor:
    - ชาย:  BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + 5
    - หญิง: BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) - 161
    """
    MALE = "male"
    FEMALE = "female"


class GoalEnum(str, PyEnum):
    """เป้าหมายของผู้ใช้ - ใช้ปรับค่า TDEE (Total Daily Energy Expenditure)
    
    - LOSE_WEIGHT:    TDEE × 0.8  (ขาดดุลแคลอรี่ 20%)
    - MAINTAIN:       TDEE × 1.0  (รักษาน้ำหนัก)
    - BUILD_MUSCLE:   TDEE × 1.15 (เกินดุลแคลอรี่ 15%)
    """
    LOSE_WEIGHT = "lose_weight"
    MAINTAIN = "maintain"
    BUILD_MUSCLE = "build_muscle"


class MealTypeEnum(str, PyEnum):
    """ประเภทมื้ออาหาร - ใช้คำนวณโควต้าแคลอรี่
    
    การแบ่งโควต้า (% ของ Daily Calorie Budget):
    - BREAKFAST: 30% - มื้อเช้า
    - LUNCH:     40% - มื้อกลางวัน (มื้อใหญ่ที่สุด)
    - DINNER:    30% - มื้อเย็น
    - SNACK:     ไม่มีโควต้าแยก (รวมในมื้อที่ใกล้ที่สุด)
    """
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class MealGradeEnum(str, PyEnum):
    """ผลการประเมินมื้ออาหาร - เกรดจากระบบ AI
    
    เกณฑ์การตัดเกรด (เทียบกับโควต้ามื้อนั้นๆ):
    - GOOD:   แคลอรี่อยู่ในช่วง ±10% ของโควต้า + สารอาหารครบถ้วน
    - MEDIUM: แคลอรี่เกิน 10-30% หรือขาดโปรตีน/สารอาหารบางตัว
    - BAD:    แคลอรี่เกิน >30% ของโควต้า หรือสารอาหารไม่สมดุลอย่างมาก
    """
    GOOD = "good"
    MEDIUM = "medium"
    BAD = "bad"


class ActivityTypeEnum(str, PyEnum):
    """ประเภทกิจกรรมที่รองรับ
    
    แต่ละประเภทมี MET value (Metabolic Equivalent of Task) ต่างกัน
    ใช้คำนวณแคลอรี่ที่เผาผลาญ: calories = MET × weight_kg × duration_hours
    """
    RUNNING = "running"
    WALKING = "walking"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    WEIGHT_TRAINING = "weight_training"
    YOGA = "yoga"
    OTHER = "other"


# ===========================================================================
# Model: User (ตารางผู้ใช้งาน)
# ===========================================================================

class User(Base):
    """
    ตาราง Users - เก็บข้อมูลพื้นฐานของผู้ใช้
    
    ข้อมูลในตารางนี้ถูกใช้ใน Core Logic หลายจุด:
    1. คำนวณ BMR (Basal Metabolic Rate) จาก weight, height, age, gender
    2. คำนวณ TDEE จาก BMR × activity_level_multiplier
    3. ปรับ Daily Calorie Budget ตาม goal (ลดน้ำหนัก/สร้างกล้ามเนื้อ)
    
    ตัวอย่างการคำนวณ:
    - ชาย อายุ 30, สูง 175cm, หนัก 80kg
    - BMR = (10 × 80) + (6.25 × 175) - (5 × 30) + 5 = 1,748.75 kcal
    - TDEE (ออกกำลังกายปานกลาง) = 1,748.75 × 1.55 = 2,710.56 kcal
    - ถ้าเป้าหมาย = ลดน้ำหนัก → Daily Budget = 2,710.56 × 0.8 = 2,168.45 kcal
    """
    __tablename__ = "users"

    # --- Primary Key ---
    # ใช้ UUID v4 เป็น PK เพื่อความปลอดภัย (ไม่สามารถเดา ID ได้)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="รหัสผู้ใช้ (UUID v4)"
    )

    # --- ข้อมูลบัญชี ---
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="ชื่อผู้ใช้สำหรับ login (ไม่ซ้ำกัน)"
    )
    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="อีเมลผู้ใช้ (ไม่ซ้ำกัน)"
    )
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="รหัสผ่านที่ผ่านการ hash แล้ว (bcrypt)"
    )

    # --- ข้อมูลร่างกาย (Body Metrics) ---
    # ใช้ Float เพื่อรองรับค่าทศนิยม เช่น น้ำหนัก 72.5 kg
    weight_kg = Column(
        Float,
        nullable=False,
        comment="น้ำหนัก (กิโลกรัม) - ใช้คำนวณ BMR"
    )
    height_cm = Column(
        Float,
        nullable=False,
        comment="ส่วนสูง (เซนติเมตร) - ใช้คำนวณ BMR"
    )
    age = Column(
        Integer,
        nullable=False,
        comment="อายุ (ปี) - ใช้คำนวณ BMR"
    )
    gender = Column(
        SAEnum(GenderEnum, name="gender_enum", create_constraint=True),
        nullable=False,
        comment="เพศ - กำหนดค่าคงที่ในสมการ BMR (+5 สำหรับชาย, -161 สำหรับหญิง)"
    )

    # --- เป้าหมาย ---
    goal = Column(
        SAEnum(GoalEnum, name="goal_enum", create_constraint=True),
        nullable=False,
        default=GoalEnum.MAINTAIN,
        comment="เป้าหมาย: ลดน้ำหนัก / รักษาน้ำหนัก / สร้างกล้ามเนื้อ"
    )

    # --- Activity Level ---
    # ค่า multiplier สำหรับคำนวณ TDEE จาก BMR
    # 1.2 = นั่งทำงาน, 1.375 = ออกกำลังกายเบา, 1.55 = ปานกลาง,
    # 1.725 = หนัก, 1.9 = หนักมาก (นักกีฬา)
    activity_level = Column(
        Float,
        nullable=False,
        default=1.55,
        comment="ระดับกิจกรรม (1.2-1.9) ใช้คูณ BMR เพื่อได้ TDEE"
    )

    # --- สถานะ ---
    is_active = Column(
        Boolean,
        default=True,
        comment="สถานะบัญชี: True = ใช้งานได้, False = ถูกระงับ"
    )

    # --- Timestamps ---
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="วันเวลาที่สร้างบัญชี"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="วันเวลาที่อัพเดทข้อมูลล่าสุด"
    )

    # --- Relationships ---
    # lazy="dynamic" ช่วยให้ query ได้ (เช่น user.meals.filter(...))
    # cascade="all, delete-orphan" ลบข้อมูลลูกเมื่อลบ user
    meals = relationship(
        "Meal",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    activities = relationship(
        "Activity",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    weekly_goals = relationship(
        "WeeklyGoal",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<User(username='{self.username}', goal='{self.goal}')>"


# ===========================================================================
# Model: Meal (ตารางมื้ออาหาร)
# ===========================================================================

class Meal(Base):
    """
    ตาราง Meals - บันทึกมื้ออาหารพร้อมผลวิเคราะห์จาก AI
    
    Flow การทำงาน:
    1. ผู้ใช้ถ่ายรูปอาหาร → อัพโหลดผ่าน API
    2. Backend ส่งรูปไปยัง Gemini Vision API
    3. AI วิเคราะห์และส่งกลับ JSON:
       {
         "food_name": "ข้าวผัดกุ้ง",
         "calories": 450,
         "protein_g": 15.2,
         "carbs_g": 55.0,
         "fat_g": 18.5
       }
    4. Backend คำนวณเกรดโดยเทียบกับโควต้ามื้อนั้น
    5. บันทึกทุกอย่างลงตาราง Meals
    
    Grading Logic:
    - คำนวณ quota = daily_calories × meal_percentage
    - ratio = actual_calories / quota
    - Good:   ratio <= 1.10 (ไม่เกิน 10%)
    - Medium: ratio <= 1.30 (เกิน 10-30%)
    - Bad:    ratio > 1.30  (เกิน 30%+)
    """
    __tablename__ = "meals"

    # --- Primary Key ---
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="รหัสมื้ออาหาร (UUID v4)"
    )

    # --- Foreign Key ---
    # เชื่อมกับตาราง users ด้วย UUID
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="รหัสผู้ใช้ที่เป็นเจ้าของมื้ออาหารนี้"
    )

    # --- ข้อมูลมื้ออาหาร ---
    meal_type = Column(
        SAEnum(MealTypeEnum, name="meal_type_enum", create_constraint=True),
        nullable=False,
        comment="ประเภทมื้อ: breakfast(30%), lunch(40%), dinner(30%), snack"
    )
    meal_date = Column(
        Date,
        nullable=False,
        default=date.today,
        index=True,
        comment="วันที่ของมื้ออาหาร (ใช้ query ข้อมูลรายวัน)"
    )

    # --- ข้อมูลรูปภาพ ---
    image_url = Column(
        Text,
        nullable=True,
        comment="URL หรือ path ของรูปภาพอาหาร (จาก file storage)"
    )

    # --- ผลวิเคราะห์จาก AI ---
    food_name = Column(
        String(200),
        nullable=True,
        comment="ชื่ออาหารที่ AI ตรวจจับได้ (เช่น 'ข้าวผัดกุ้ง')"
    )
    calories = Column(
        Float,
        nullable=True,
        default=0.0,
        comment="แคลอรี่รวม (kcal) - ผลจาก AI analysis"
    )
    protein_g = Column(
        Float,
        nullable=True,
        default=0.0,
        comment="โปรตีน (กรัม) - ผลจาก AI analysis"
    )
    carbs_g = Column(
        Float,
        nullable=True,
        default=0.0,
        comment="คาร์โบไฮเดรต (กรัม) - ผลจาก AI analysis"
    )
    fat_g = Column(
        Float,
        nullable=True,
        default=0.0,
        comment="ไขมัน (กรัม) - ผลจาก AI analysis"
    )

    # --- ผลการประเมิน ---
    grade = Column(
        SAEnum(MealGradeEnum, name="meal_grade_enum", create_constraint=True),
        nullable=True,
        comment="เกรดมื้ออาหาร: good/medium/bad (เทียบกับโควต้า)"
    )
    quota_calories = Column(
        Float,
        nullable=True,
        comment="โควต้าแคลอรี่ของมื้อนี้ (คำนวณจาก daily budget × %)"
    )

    # --- AI Response (เก็บ raw response เพื่อ debug) ---
    ai_raw_response = Column(
        Text,
        nullable=True,
        comment="Raw JSON response จาก Gemini Vision API (สำหรับ debugging)"
    )

    # --- Timestamps ---
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="วันเวลาที่บันทึกมื้ออาหาร"
    )

    # --- Relationship ---
    user = relationship("User", back_populates="meals")

    def __repr__(self):
        return (
            f"<Meal(food='{self.food_name}', "
            f"calories={self.calories}, grade='{self.grade}')>"
        )


# ===========================================================================
# Model: Activity (ตารางกิจกรรม)
# ===========================================================================

class Activity(Base):
    """
    ตาราง Activities - บันทึกกิจกรรมออกกำลังกายรายวัน
    
    ใช้ร่วมกับ WeeklyGoal:
    - ผู้ใช้ตั้ง WeeklyGoal (เช่น วิ่งรวม 30 km/สัปดาห์)
    - บันทึก Activity ทุกวัน (เช่น วันนี้วิ่ง 5 km)
    - ระบบคำนวณ remaining และ recommend ว่าพรุ่งนี้ต้องทำเท่าไหร่
    
    Calorie Burn Estimation:
    - ใช้ MET (Metabolic Equivalent of Task) values:
      Running: 9.8, Walking: 3.5, Cycling: 7.5,
      Swimming: 8.0, Weight Training: 6.0, Yoga: 3.0
    - สูตร: calories_burned = MET × weight_kg × duration_hours
    """
    __tablename__ = "activities"

    # --- Primary Key ---
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="รหัสกิจกรรม (UUID v4)"
    )

    # --- Foreign Key ---
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="รหัสผู้ใช้ที่บันทึกกิจกรรม"
    )

    # --- ข้อมูลกิจกรรม ---
    activity_type = Column(
        SAEnum(ActivityTypeEnum, name="activity_type_enum", create_constraint=True),
        nullable=False,
        comment="ประเภทกิจกรรม (running, walking, cycling, etc.)"
    )
    activity_date = Column(
        Date,
        nullable=False,
        default=date.today,
        index=True,
        comment="วันที่ทำกิจกรรม"
    )
    duration_minutes = Column(
        Integer,
        nullable=False,
        comment="ระยะเวลา (นาที) - ใช้คำนวณแคลอรี่ที่เผาผลาญ"
    )
    distance_km = Column(
        Float,
        nullable=True,
        comment="ระยะทาง (กิโลเมตร) - ถ้ามี (เช่น วิ่ง, ปั่นจักรยาน)"
    )
    calories_burned = Column(
        Float,
        nullable=True,
        comment="แคลอรี่ที่เผาผลาญ (kcal) - คำนวณจาก MET × weight × duration"
    )

    # --- บันทึกเพิ่มเติม ---
    notes = Column(
        Text,
        nullable=True,
        comment="บันทึกเพิ่มเติม (เช่น 'วิ่งได้เร็วขึ้นกว่าเมื่อวาน')"
    )

    # --- Timestamps ---
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="วันเวลาที่บันทึกกิจกรรม"
    )

    # --- Relationship ---
    user = relationship("User", back_populates="activities")

    def __repr__(self):
        return (
            f"<Activity(type='{self.activity_type}', "
            f"duration={self.duration_minutes}min, date='{self.activity_date}')>"
        )


# ===========================================================================
# Model: WeeklyGoal (ตารางเป้าหมายรายสัปดาห์)
# ===========================================================================

class WeeklyGoal(Base):
    """
    ตาราง WeeklyGoals - เป้าหมายรายสัปดาห์และระบบแนะนำอัจฉริยะ
    
    Dynamic Calculation Flow:
    1. ผู้ใช้ตั้งเป้าหมาย: "วิ่ง 30 km ภายในสัปดาห์นี้"
       → target_value = 30, target_unit = "km"
    
    2. ผู้ใช้บันทึกทุกวัน → current_value อัพเดทอัตโนมัติ
       - จันทร์: วิ่ง 5 km  → current_value = 5
       - อังคาร: วิ่ง 4 km  → current_value = 9
       - พุธ:   วิ่ง 6 km  → current_value = 15
    
    3. Recommendation Logic:
       remaining = target_value - current_value  →  30 - 15 = 15 km
       days_left = end_date - today              →  4 วัน (พฤ-อา)
       daily_recommendation = remaining / days_left → 15 / 4 = 3.75 km/วัน
       
       → แนะนำ: "พรุ่งนี้คุณต้องวิ่ง 3.75 km เพื่อให้ทันเป้าหมาย"
    
    4. ถ้า current_value >= target_value → is_completed = True 🎉
    """
    __tablename__ = "weekly_goals"

    # --- Primary Key ---
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="รหัสเป้าหมาย (UUID v4)"
    )

    # --- Foreign Key ---
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="รหัสผู้ใช้ที่ตั้งเป้าหมาย"
    )

    # --- ช่วงเวลา ---
    week_start_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="วันจันทร์แรกของสัปดาห์ (ใช้เป็น anchor date)"
    )
    week_end_date = Column(
        Date,
        nullable=False,
        comment="วันอาทิตย์สุดท้ายของสัปดาห์"
    )

    # --- เป้าหมาย ---
    activity_type = Column(
        SAEnum(ActivityTypeEnum, name="activity_type_enum", create_constraint=True),
        nullable=False,
        comment="ประเภทกิจกรรมที่ตั้งเป้า"
    )
    target_value = Column(
        Float,
        nullable=False,
        comment="ค่าเป้าหมาย (เช่น 30 km, 300 นาที, 5 ครั้ง)"
    )
    target_unit = Column(
        String(20),
        nullable=False,
        default="minutes",
        comment="หน่วยของเป้าหมาย: 'km', 'minutes', 'sessions', 'calories'"
    )

    # --- ความคืบหน้า ---
    current_value = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="ค่าที่ทำได้แล้ว (อัพเดทอัตโนมัติเมื่อบันทึก Activity)"
    )
    is_completed = Column(
        Boolean,
        default=False,
        comment="สถานะบรรลุเป้าหมาย: True เมื่อ current_value >= target_value"
    )

    # --- Timestamps ---
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="วันเวลาที่สร้างเป้าหมาย"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="วันเวลาที่อัพเดทล่าสุด"
    )

    # --- Relationship ---
    user = relationship("User", back_populates="weekly_goals")

    def __repr__(self):
        return (
            f"<WeeklyGoal(type='{self.activity_type}', "
            f"progress={self.current_value}/{self.target_value} {self.target_unit})>"
        )
