-- ===========================================================================
-- init.sql - สคริปต์ตั้งค่าฐานข้อมูล PostgreSQL
-- ===========================================================================
--
-- ใช้สำหรับสร้าง database และ user เบื้องต้น
-- รันด้วย: psql -U postgres -f init.sql
--
-- หมายเหตุ: 
-- - SQLAlchemy จะสร้างตารางอัตโนมัติจาก models.py
-- - ไฟล์นี้สร้างเฉพาะ database และ user เท่านั้น
-- ===========================================================================

-- สร้าง database (ถ้ายังไม่มี)
SELECT 'CREATE DATABASE self_dev_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'self_dev_db')\gexec

-- สร้าง user สำหรับ application (optional - ถ้าไม่ต้องการใช้ postgres user)
-- CREATE USER self_dev_user WITH PASSWORD 'your_secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE self_dev_db TO self_dev_user;

-- เชื่อมต่อกับ database ที่สร้าง
\c self_dev_db

-- เปิดใช้ UUID extension (ถ้ายังไม่ได้เปิด)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- แสดงผลลัพธ์
\echo '✅ Database self_dev_db initialized successfully!'
\echo '📌 Run the FastAPI app to auto-create tables from models.py'
