#!/usr/bin/env bash
# ===========================================================================
# build.sh - Build script สำหรับ Render.com deployment
# ===========================================================================
# Render จะรัน script นี้เมื่อ deploy ครั้งใหม่
# มันจะ:
# 1. ติดตั้ง Node.js dependencies + build Vue.js frontend
# 2. ติดตั้ง Python dependencies สำหรับ backend
# ===========================================================================

set -o errexit  # หยุดทันทีถ้ามี error

echo "=========================================="
echo "🔨 Building Self-Development App..."
echo "=========================================="

# --- Step 1: Build Frontend ---
echo ""
echo "📦 Step 1: Building Vue.js Frontend..."
echo "---"

cd frontend
npm install
npm run build
cd ..

echo "✅ Frontend built successfully!"
echo ""

# --- Step 2: Install Backend Dependencies ---
echo "📦 Step 2: Installing Python Dependencies..."
echo "---"

cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo "✅ Backend dependencies installed!"
echo ""
echo "=========================================="
echo "🎉 Build complete!"
echo "=========================================="
