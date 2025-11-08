#!/bin/bash
echo "Starting AlbumDuel backend..."
cd backend
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..
echo "Starting AlbumDuel frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo "Application started. Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop."
wait
