# ===========================================================================
# Dockerfile - Self-Development API (Backend)
# ===========================================================================
# Multi-stage build เพื่อให้ image มีขนาดเล็กและปลอดภัย
#
# Build:  docker build -t self-dev-api .
# Run:    docker run -p 8000:8000 --env-file .env self-dev-api
# ===========================================================================

# ---------------------------------------------------------------------------
# Stage 1: Base image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base

# ป้องกัน Python สร้าง .pyc files และ buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# สร้าง non-root user สำหรับ security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# ---------------------------------------------------------------------------
# Stage 2: Install dependencies
# ---------------------------------------------------------------------------
FROM base AS dependencies

# ติดตั้ง system dependencies ที่จำเป็นสำหรับ psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# คัดลอก requirements.txt ก่อน เพื่อใช้ Docker layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 3: Production image
# ---------------------------------------------------------------------------
FROM base AS production

# ติดตั้ง runtime dependency สำหรับ PostgreSQL
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# คัดลอก installed packages จาก dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# คัดลอก source code
COPY . .

# เปลี่ยนเป็น non-root user
RUN chown -R appuser:appuser /app
USER appuser

# เปิด port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# รัน FastAPI ด้วย Uvicorn
# - --host 0.0.0.0: รับ connection จากทุก interface
# - --workers 4: ใช้ 4 worker processes สำหรับ production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
