# Self-Development Web Application

🏋️ ระบบจัดการเป้าหมายและสุขภาพส่วนบุคคล

## Features
- 📸 **Food AI Vision** — ถ่ายรูปอาหาร → AI วิเคราะห์แคลอรี่อัตโนมัติ
- 🏃 **Activity Tracker** — บันทึกการออกกำลังกาย + คำนวณแคลอรี่ที่เผาผลาญ
- 🎯 **Weekly Goals** — ตั้งเป้าหมายรายสัปดาห์ + คำแนะนำอัจฉริยะ
- 📊 **BMR Calculator** — คำนวณแคลอรี่ที่ร่างกายต้องการ

## Tech Stack
- **Frontend**: Vue.js 3 + Vite
- **Backend**: Python FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **AI**: Google Gemini Vision

## Quick Start (Local)
```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/self-dev-app.git
cd self-dev-app

# 2. Start database
docker run -d --name selfdev-pg \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=self_dev_db \
  -p 5432:5432 postgres:16-alpine

# 3. Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 4. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Deploy to Render
1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo
4. Render reads `render.yaml` automatically
5. Set `GOOGLE_API_KEY` in environment variables
6. Deploy! 🚀
