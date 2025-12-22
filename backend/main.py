from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from backend.database import engine, get_db
from backend.models import Base, Issue
from backend.ai_service import generate_action_plan
import json
import os
import shutil
import uuid
import asyncio
from fastapi import Depends
from contextlib import asynccontextmanager
from backend.bot import run_bot

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Telegram Bot
    bot_app = await run_bot()
    yield
    # Shutdown: Stop Telegram Bot
    if bot_app:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()

app = FastAPI(title="VishwaGuru Backend", lifespan=lifespan)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

def save_file_blocking(file_obj, path):
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file_obj, buffer)

def save_issue_db(db: Session, issue: Issue):
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue

@app.post("/api/issues")
async def create_issue(
    description: str = Form(...),
    category: str = Form(...),
    user_email: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Save image if provided
    image_path = None
    if image:
        upload_dir = "data/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        # Generate unique filename
        filename = f"{uuid.uuid4()}_{image.filename}"
        image_path = os.path.join(upload_dir, filename)

        # Offload blocking file I/O to threadpool
        await run_in_threadpool(save_file_blocking, image.file, image_path)

    # Save to DB
    new_issue = Issue(
        description=description,
        category=category,
        image_path=image_path,
        source="web",
        user_email=user_email
    )

    # Offload blocking DB operations to threadpool
    await run_in_threadpool(save_issue_db, db, new_issue)

    # Generate Action Plan (AI)
    action_plan = await generate_action_plan(description, category, image_path)

    return {
        "id": new_issue.id,
        "message": "Issue reported successfully",
        "action_plan": action_plan
    }

@app.get("/api/responsibility-map")
def get_responsibility_map():
    # In a real app, this might read from the file or database
    # For MVP, we can return the structure directly or read the file

    # Assuming the data folder is at the root level relative to where backend is run
    # Adjust path as necessary. If running from root, it is "data/responsibility_map.json"
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "responsibility_map.json")

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"error": "Data file not found"}

# Serve Frontend (Must be last)
# Mount the 'dist' directory as a static directory
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{catchall:path}")
    async def serve_react_app(catchall: str):
        # Check if file exists in dist (e.g., favicon.ico)
        file_path = os.path.join(frontend_dist, catchall)
        if os.path.exists(file_path) and os.path.isfile(file_path):
             return FileResponse(file_path)

        # Otherwise return index.html for SPA
        return FileResponse(os.path.join(frontend_dist, "index.html"))
