#!/bin/bash
set -e
echo "==================================================="
echo " Starting CurriculumAI Studio Production Suite     "
echo "==================================================="

if command -v docker-compose &> /dev/null; then
    echo "Launching full stack via Docker Compose..."
    docker-compose up --build -d
    echo "Frontend: http://localhost:3000"
    echo "Backend:  http://localhost:8000/api/v1/docs"
elif command -v uvicorn &> /dev/null; then
    echo "Launching FastAPI backend standalone..."
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Please install Docker or Python dependencies: pip install -r backend/requirements.txt"
fi
