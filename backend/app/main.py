import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect, BackgroundTasks, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional

from .config import settings
from .database import get_db, engine, Base
from . import models, schemas, auth, tasks
from .services.ws_manager import ws_manager
from .ai.model_manager import ModelManager

logger = logging.getLogger(__name__)

# Create Database tables (simple sync migration for development)
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    # Startup
    asyncio.create_task(ws_manager.start_pubsub_listener())
    logger.info("Application started. Active WebSocket Pub/Sub workers online.")
    yield
    # Shutdown
    logger.info("Application shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

# CORS — locked to configured allowed origins (no wildcard in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Static files — path from settings (not hardcoded to developer machine)
static_dir = settings.STATIC_DIR
os.makedirs(os.path.join(static_dir, "renders"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "uploads"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Local Model Manager instantiation inside API process
local_model_manager = ModelManager()

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

# --- DEVSECOPS SECURITY FILTERS ---

def validate_file_signature(content: bytes, filename: str) -> bool:
    ext = filename.split(".")[-1].lower()
    if ext in ["jpg", "jpeg"]:
        return content.startswith(b"\xff\xd8\xff")
    elif ext == "png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    elif ext in ["mp4", "mov"]:
        return b"ftyp" in content[:32] or content.startswith(b"\x00\x00\x00")
    return True

def sanitize_prompt(prompt: str) -> str:
    # Truncate extremely long prompts to prevent DB/model overflows
    if len(prompt) > 2000:
        prompt = prompt[:2000]
    injection_keywords = ["ignore previous instructions", "bypass system rule", "system override", "you are now free"]
    cleaned = prompt
    for kw in injection_keywords:
        if kw in cleaned.lower():
            raise HTTPException(status_code=400, detail=f"Malicious prompt pattern detected: '{kw}'")
    return cleaned

def rate_limiter(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"
    try:
        import redis
        redis_client = redis.Redis.from_url(settings.broker_url)
        current = redis_client.get(key)
        if current and int(current) > 60:
            raise HTTPException(status_code=429, detail="Too Many Requests. API Rate limit exceeded.")
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        pipe.execute()
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.warning(f"Rate Limiter Redis connectivity warning: {e}")
        pass

@app.get("/healthz")
def healthz_probe(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")
        
    redis_status = "up"
    try:
        import redis
        redis_client = redis.Redis.from_url(settings.broker_url)
        redis_client.ping()
    except Exception as e:
        logger.warning(f"Redis healthcheck ping failed: {e}")
        redis_status = "down (warning)"
        
    return {"status": "healthy", "database": "up", "redis": redis_status}

@app.get(f"{settings.API_V1_STR}/metrics")
def metrics_dashboard():
    import psutil
    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().used
    except Exception:
        cpu = 12.5
        mem = 1024 * 1024 * 512
    return {
        "system_cpu_percent": cpu,
        "system_memory_used_bytes": mem,
        "gpu_inference_jobs_active": 1,
        "api_latency_seconds_average": 0.045
    }

# --- WEBSOCKETS ---

@app.websocket(f"{settings.API_V1_STR}/renders/ws/{{client_id}}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket route mapping connection state to connection manager pool."""
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            # Read messages from socket to keep loop alive
            data = await websocket.receive_text()
            # Simple heartbeat handler
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket execution error for client {client_id}: {e}")
        ws_manager.disconnect(websocket, client_id)

# --- AUTHENTICATION ---

@app.post(f"{settings.API_V1_STR}/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_email = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = auth.get_password_hash(user_in.password)
    new_user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        credits=100.0,
        is_active=True,
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post(f"{settings.API_V1_STR}/auth/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get(f"{settings.API_V1_STR}/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

# --- PROJECTS ---

@app.post(f"{settings.API_V1_STR}/projects", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    db_project = models.Project(**project.model_dump(), owner_id=current_user.id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get(f"{settings.API_V1_STR}/projects", response_model=List[schemas.ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.Project).filter(models.Project.owner_id == current_user.id).offset(skip).limit(limit).all()

@app.get(f"{settings.API_V1_STR}/projects/{{project_id}}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put(f"{settings.API_V1_STR}/projects/{{project_id}}", response_model=schemas.ProjectResponse)
def update_project(project_id: int, project_in: schemas.ProjectUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in project_in.model_dump().items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project

@app.delete(f"{settings.API_V1_STR}/projects/{{project_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None

# --- ASSETS ---

@app.post(f"{settings.API_V1_STR}/assets/upload", response_model=schemas.AssetResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limiter)])
async def upload_asset(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    if project_id:
        proj = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

    contents = await file.read()
    if not validate_file_signature(contents, file.filename):
        raise HTTPException(status_code=400, detail="Invalid file signature signature verification failed.")
    file_size = len(contents)
    filename = f"{current_user.id}_{int(os.urandom(4).hex(), 16)}_{file.filename}"
    
    storage_path = ""
    try:
        s3 = tasks.get_s3_client()
        try:
            s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        except Exception:
            s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
            
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=filename,
            Body=contents,
            ContentType=file.content_type
        )
        storage_path = f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{filename}"
    except Exception as e:
        local_path = os.path.join(static_dir, "uploads", filename)
        with open(local_path, "wb") as f:
            f.write(contents)
        storage_path = f"/static/uploads/{filename}"

    new_asset = models.Asset(
        filename=filename,
        original_name=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        storage_path=storage_path,
        owner_id=current_user.id,
        project_id=project_id
    )
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)
    return new_asset

@app.get(f"{settings.API_V1_STR}/assets", response_model=List[schemas.AssetResponse])
def list_assets(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    query = db.query(models.Asset).filter(models.Asset.owner_id == current_user.id)
    if project_id:
        query = query.filter(models.Asset.project_id == project_id)
    return query.offset(skip).limit(limit).all()

# --- RENDERING ---

@app.post(f"{settings.API_V1_STR}/renders/trigger", response_model=schemas.RenderJobResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limiter)])
def trigger_render(
    job_in: schemas.RenderJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    sanitize_prompt(job_in.prompt)
    if job_in.input_asset_id:
        asset = db.query(models.Asset).filter(models.Asset.id == job_in.input_asset_id, models.Asset.owner_id == current_user.id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Input asset not found")

    if job_in.project_id:
        proj = db.query(models.Project).filter(models.Project.id == job_in.project_id, models.Project.owner_id == current_user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

    # Dynamic generation credit calculation
    cost = 10.0 + (job_in.duration * 0.5) + (job_in.steps * 0.1)
    if current_user.credits < cost:
        raise HTTPException(status_code=400, detail="Insufficient credits")

    new_job = models.RenderJob(
        job_type=job_in.job_type,
        status="PENDING",
        progress=0,
        prompt=job_in.prompt,
        negative_prompt=job_in.negative_prompt,
        aspect_ratio=job_in.aspect_ratio,
        duration=job_in.duration,
        cost=cost,
        steps=job_in.steps,
        cfg_scale=job_in.cfg_scale,
        seed=job_in.seed,
        motion_strength=job_in.motion_strength,
        fps=job_in.fps,
        model_version=job_in.model_version,
        input_asset_id=job_in.input_asset_id,
        user_id=current_user.id,
        project_id=job_in.project_id
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Dispatch to Celery — fallback to FastAPI BackgroundTasks if broker (Redis) is unavailable
    try:
        tasks.render_video_task.delay(new_job.id)
    except Exception as e:
        logger.warning(f"Celery broker unavailable — falling back to FastAPI BackgroundTasks for job {new_job.id}: {e}")
        background_tasks.add_task(tasks.render_video_task, None, new_job.id)

    # Broadcast initial queued progress — graceful fallback
    try:
        from .tasks import broadcast_progress
        broadcast_progress(new_job.user_id, new_job.id, 0, "PENDING")
    except Exception as e:
        logger.warning(f"WebSocket broadcast failed for job {new_job.id}: {e}")

    return new_job

@app.get(f"{settings.API_V1_STR}/renders", response_model=List[schemas.RenderJobResponse])
def list_renders(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    query = db.query(models.RenderJob).filter(models.RenderJob.user_id == current_user.id)
    if project_id:
        query = query.filter(models.RenderJob.project_id == project_id)
    return query.offset(skip).limit(limit).all()

@app.get(f"{settings.API_V1_STR}/renders/{{job_id}}", response_model=schemas.RenderJobResponse)
def get_render_job(job_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    job = db.query(models.RenderJob).filter(models.RenderJob.id == job_id, models.RenderJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")
    return job

@app.post(f"{settings.API_V1_STR}/renders/{{job_id}}/cancel", response_model=schemas.RenderJobResponse)
def cancel_render(job_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    """Cancel a pending or running render job."""
    job = db.query(models.RenderJob).filter(models.RenderJob.id == job_id, models.RenderJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")
    
    if job.status not in ["PENDING", "RUNNING"]:
        raise HTTPException(status_code=400, detail="Only pending or running jobs can be cancelled")
        
    job.status = "CANCELLED"
    db.commit()
    db.refresh(job)
    
    try:
        from .tasks import broadcast_progress
        broadcast_progress(job.user_id, job.id, job.progress, "CANCELLED", error_message="Render cancelled by user.")
    except Exception as e:
        logger.warning(f"WebSocket broadcast failed for job cancel {job.id}: {e}")
    
    return job

@app.post(f"{settings.API_V1_STR}/renders/{{job_id}}/retry", response_model=schemas.RenderJobResponse)
def retry_render(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Retry a failed or cancelled generation job."""
    job = db.query(models.RenderJob).filter(models.RenderJob.id == job_id, models.RenderJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")
        
    if job.status not in ["FAILED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Only failed or cancelled jobs can be retried")
        
    job.status = "PENDING"
    job.progress = 0
    job.error_message = None
    db.commit()
    db.refresh(job)
    
    # Re-queue task
    try:
        tasks.render_video_task.delay(job.id)
    except Exception as e:
        logger.warning(f"Celery broker unavailable — falling back to FastAPI BackgroundTasks for job retry {job.id}: {e}")
        background_tasks.add_task(tasks.render_video_task, None, job.id)
    
    try:
        from .tasks import broadcast_progress
        broadcast_progress(job.user_id, job.id, 0, "PENDING")
    except Exception as e:
        logger.warning(f"WebSocket broadcast failed for job retry {job.id}: {e}")
    
    return job

# --- MODEL MANAGEMENT ---

@app.get(f"{settings.API_V1_STR}/models", response_model=List[schemas.ModelInfo])
def get_installed_models(current_user: models.User = Depends(auth.get_current_active_user)):
    """List registered models along with their load statuses."""
    models_dict = local_model_manager.list_models()
    return [
        schemas.ModelInfo(id=mid, **details)
        for mid, details in models_dict.items()
    ]

@app.post(f"{settings.API_V1_STR}/models/download", response_model=schemas.ModelInfo)
def download_model(request: schemas.ModelSwitchRequest, background_tasks: BackgroundTasks, current_user: models.User = Depends(auth.get_current_active_user)):
    """Asynchronously download and cache model weight parameters from Hugging Face."""
    models_dict = local_model_manager.list_models()
    if request.model_id not in models_dict:
         raise HTTPException(status_code=404, detail="Model ID not registered")
         
    # Load task to background thread pool
    background_tasks.add_task(local_model_manager.load_model, request.model_id)
    
    # Fetch updated details
    info = models_dict[request.model_id]
    return schemas.ModelInfo(id=request.model_id, **info)

@app.post(f"{settings.API_V1_STR}/models/switch", response_model=schemas.ModelInfo)
def switch_active_model(request: schemas.ModelSwitchRequest, current_user: models.User = Depends(auth.get_current_active_user)):
    """Swap the currently active diffusion pipeline in the ModelManager memory pool."""
    try:
        local_model_manager.switch_active_model(request.model_id)
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
         
    models_dict = local_model_manager.list_models()
    return schemas.ModelInfo(id=request.model_id, **models_dict[request.model_id])

@app.delete(f"{settings.API_V1_STR}/models/{{model_id}}", response_model=schemas.MessageResponse)
def delete_model_cache(model_id: str, current_user: models.User = Depends(auth.get_current_active_user)):
    """Delete a model's local cached safetensor files from the disk."""
    success = local_model_manager.delete_cached_files(model_id)
    if not success:
         raise HTTPException(status_code=404, detail="Model cache files not found or ID invalid")
    return schemas.MessageResponse(status="success", message=f"Cache files deleted for model {model_id}.")

# --- PROMPT ENGINE ---

@app.post(f"{settings.API_V1_STR}/prompt/enhance", response_model=schemas.PromptStructured)
def enhance_prompt(
    request: schemas.PromptEnhanceRequest,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    enhanced_dict = tasks.enhance_prompt_task(request.prompt)
    return enhanced_dict

# --- STORYBOARD & TIMELINE ENDPOINTS ---

@app.post(f"{settings.API_V1_STR}/storyboards", response_model=schemas.StoryboardResponse, status_code=status.HTTP_201_CREATED)
def create_storyboard(
    sb_in: schemas.StoryboardCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    if sb_in.project_id:
        proj = db.query(models.Project).filter(models.Project.id == sb_in.project_id, models.Project.owner_id == current_user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

    storyboard = models.Storyboard(
        name=sb_in.name,
        description=sb_in.description,
        owner_id=current_user.id,
        project_id=sb_in.project_id,
        status="PENDING",
        progress=0
    )
    db.add(storyboard)
    db.commit()
    db.refresh(storyboard)

    timeline = models.Timeline(storyboard_id=storyboard.id)
    db.add(timeline)
    db.commit()
    db.refresh(timeline)

    video_layer = models.Layer(timeline_id=timeline.id, name="Video Track", order=0, layer_type="video")
    audio_layer = models.Layer(timeline_id=timeline.id, name="Audio Track", order=1, layer_type="audio")
    text_layer = models.Layer(timeline_id=timeline.id, name="Subtitle Track", order=2, layer_type="text")
    db.add_all([video_layer, audio_layer, text_layer])
    db.commit()

    db.refresh(storyboard)
    return storyboard

@app.get(f"{settings.API_V1_STR}/storyboards", response_model=List[schemas.StoryboardResponse])
def list_storyboards(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    query = db.query(models.Storyboard).filter(models.Storyboard.owner_id == current_user.id)
    if project_id:
        query = query.filter(models.Storyboard.project_id == project_id)
    return query.all()

@app.get(f"{settings.API_V1_STR}/storyboards/{{storyboard_id}}", response_model=schemas.StoryboardResponse)
def get_storyboard(
    storyboard_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    sb = db.query(models.Storyboard).filter(models.Storyboard.id == storyboard_id, models.Storyboard.owner_id == current_user.id).first()
    if not sb:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    return sb

@app.delete(f"{settings.API_V1_STR}/storyboards/{{storyboard_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_storyboard(
    storyboard_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    sb = db.query(models.Storyboard).filter(models.Storyboard.id == storyboard_id, models.Storyboard.owner_id == current_user.id).first()
    if not sb:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    db.delete(sb)
    db.commit()
    return None

@app.post(f"{settings.API_V1_STR}/storyboards/{{storyboard_id}}/render", response_model=schemas.StoryboardResponse)
def trigger_storyboard_render(
    storyboard_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    sb = db.query(models.Storyboard).filter(models.Storyboard.id == storyboard_id, models.Storyboard.owner_id == current_user.id).first()
    if not sb:
        raise HTTPException(status_code=404, detail="Storyboard not found")
        
    sb.status = "PENDING"
    sb.progress = 0
    sb.error_message = None
    db.commit()
    db.refresh(sb)
    
    try:
        tasks.render_storyboard_task.delay(sb.id)
    except Exception as e:
        logger.warning(f"Celery broker unavailable — falling back to FastAPI BackgroundTasks for storyboard render {sb.id}: {e}")
        background_tasks.add_task(tasks.render_storyboard_task, sb.id)
    return sb

# --- SCENES & SHOTS ---

@app.post(f"{settings.API_V1_STR}/storyboards/{{storyboard_id}}/scenes", response_model=schemas.SceneResponse)
def create_scene(
    storyboard_id: int,
    scene_in: schemas.SceneCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    sb = db.query(models.Storyboard).filter(models.Storyboard.id == storyboard_id, models.Storyboard.owner_id == current_user.id).first()
    if not sb:
        raise HTTPException(status_code=404, detail="Storyboard not found")
        
    scene = models.Scene(**scene_in.model_dump(), storyboard_id=storyboard_id)
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return scene

@app.post(f"{settings.API_V1_STR}/scenes/{{scene_id}}/shots", response_model=schemas.ShotResponse)
def create_shot(
    scene_id: int,
    shot_in: schemas.ShotCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    scene = db.query(models.Scene).filter(models.Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
        
    sb = db.query(models.Storyboard).filter(models.Storyboard.id == scene.storyboard_id, models.Storyboard.owner_id == current_user.id).first()
    if not sb:
        raise HTTPException(status_code=403, detail="Not authorized to edit this storyboard")
        
    shot = models.Shot(**shot_in.model_dump(), scene_id=scene_id)
    db.add(shot)
    db.commit()
    db.refresh(shot)
    return shot

@app.delete(f"{settings.API_V1_STR}/scenes/{{scene_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scene(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    scene = db.query(models.Scene).filter(models.Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
        
    sb = db.query(models.Storyboard).filter(models.Storyboard.id == scene.storyboard_id, models.Storyboard.owner_id == current_user.id).first()
    if not sb:
        raise HTTPException(status_code=403, detail="Not authorized to edit this storyboard")
        
    db.delete(scene)
    db.commit()
    return None

@app.delete(f"{settings.API_V1_STR}/shots/{{shot_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shot(
    shot_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    shot = db.query(models.Shot).filter(models.Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
        
    scene = db.query(models.Scene).filter(models.Scene.id == shot.scene_id).first()
    sb = db.query(models.Storyboard).filter(models.Storyboard.id == scene.storyboard_id, models.Storyboard.owner_id == current_user.id).first()
    if not sb:
        raise HTTPException(status_code=403, detail="Not authorized to edit this storyboard")
        
    db.delete(shot)
    db.commit()
    return None

# --- TIMELINE CONTROLS ---

@app.get(f"{settings.API_V1_STR}/storyboards/{{storyboard_id}}/timeline", response_model=schemas.TimelineResponse)
def get_storyboard_timeline(
    storyboard_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    sb = db.query(models.Storyboard).filter(models.Storyboard.id == storyboard_id, models.Storyboard.owner_id == current_user.id).first()
    if not sb:
        raise HTTPException(status_code=404, detail="Storyboard not found")
        
    timeline = db.query(models.Timeline).filter(models.Timeline.storyboard_id == storyboard_id).first()
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return timeline

@app.post(f"{settings.API_V1_STR}/layers/{{layer_id}}/items", response_model=schemas.TimelineItemResponse)
def add_timeline_item(
    layer_id: int,
    item_in: schemas.TimelineItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    layer = db.query(models.Layer).filter(models.Layer.id == layer_id).first()
    if not layer:
         raise HTTPException(status_code=404, detail="Layer not found")
         
    timeline = db.query(models.Timeline).filter(models.Timeline.id == layer.timeline_id).first()
    sb = db.query(models.Storyboard).filter(models.Storyboard.id == timeline.storyboard_id, models.Storyboard.owner_id == current_user.id).first()
    if not sb:
         raise HTTPException(status_code=403, detail="Not authorized to edit this timeline")
         
    item = models.TimelineItem(**item_in.model_dump(), layer_id=layer_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.delete(f"{settings.API_V1_STR}/timeline-items/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timeline_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    item = db.query(models.TimelineItem).filter(models.TimelineItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Timeline item not found")
        
    layer = db.query(models.Layer).filter(models.Layer.id == item.layer_id).first()
    timeline = db.query(models.Timeline).filter(models.Timeline.id == layer.timeline_id).first()
    sb = db.query(models.Storyboard).filter(models.Storyboard.id == timeline.storyboard_id, models.Storyboard.owner_id == current_user.id).first()
    if not sb:
         raise HTTPException(status_code=403, detail="Not authorized to edit this timeline")
         
    db.delete(item)
    db.commit()
    return None

# --- AUDIO INTELLIGENCE ENDPOINTS ---

@app.post(f"{settings.API_V1_STR}/audio/voices", response_model=schemas.VoiceProfileResponse, status_code=status.HTTP_201_CREATED)
def create_voice_profile(
    voice_in: schemas.VoiceProfileCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    profile = models.VoiceProfile(
        name=voice_in.name,
        language=voice_in.language,
        owner_id=current_user.id
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@app.get(f"{settings.API_V1_STR}/audio/voices", response_model=List[schemas.VoiceProfileResponse])
def list_voice_profiles(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.VoiceProfile).filter(models.VoiceProfile.owner_id == current_user.id).offset(skip).limit(limit).all()

@app.delete(f"{settings.API_V1_STR}/audio/voices/{{voice_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_voice_profile(
    voice_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    profile = db.query(models.VoiceProfile).filter(
        models.VoiceProfile.id == voice_id,
        models.VoiceProfile.owner_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    db.delete(profile)
    db.commit()
    return None

@app.post(f"{settings.API_V1_STR}/audio/jobs", response_model=schemas.AudioJobResponse, status_code=status.HTTP_201_CREATED)
def trigger_audio_job(
    job_in: schemas.AudioJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Verify voice profile if provided
    if job_in.voice_profile_id:
        vp = db.query(models.VoiceProfile).filter(
            models.VoiceProfile.id == job_in.voice_profile_id,
            models.VoiceProfile.owner_id == current_user.id
        ).first()
        if not vp:
            raise HTTPException(status_code=404, detail="Voice profile not found")

    job = models.AudioJob(
        job_type=job_in.job_type,
        prompt=job_in.prompt,
        voice_profile_id=job_in.voice_profile_id,
        user_id=current_user.id,
        status="PENDING",
        progress=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Trigger Celery Background Task — fallback to FastAPI BackgroundTasks if broker is down
    try:
        tasks.process_audio_task.delay(job.id)
    except Exception as e:
        logger.warning(f"Celery broker unavailable — falling back to FastAPI BackgroundTasks for audio job {job.id}: {e}")
        background_tasks.add_task(tasks.process_audio_task, job.id)
    return job

@app.get(f"{settings.API_V1_STR}/audio/jobs/{{job_id}}", response_model=schemas.AudioJobResponse)
def get_audio_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    job = db.query(models.AudioJob).filter(
        models.AudioJob.id == job_id,
        models.AudioJob.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Audio job not found")
    return job

@app.get(f"{settings.API_V1_STR}/audio/subtitles", response_model=List[schemas.SubtitleResponse])
def list_subtitles(
    storyboard_id: Optional[int] = None,
    render_job_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    if storyboard_id:
        sb = db.query(models.Storyboard).filter(
            models.Storyboard.id == storyboard_id,
            models.Storyboard.owner_id == current_user.id
        ).first()
        if not sb:
            raise HTTPException(status_code=403, detail="Not authorized to access this storyboard")
        return db.query(models.Subtitle).filter(models.Subtitle.storyboard_id == storyboard_id).offset(skip).limit(limit).all()
        
    if render_job_id:
        job = db.query(models.RenderJob).filter(
            models.RenderJob.id == render_job_id,
            models.RenderJob.user_id == current_user.id
        ).first()
        if not job:
            raise HTTPException(status_code=403, detail="Not authorized to access this render job")
        return db.query(models.Subtitle).filter(models.Subtitle.render_job_id == render_job_id).offset(skip).limit(limit).all()
        
    sb_ids = [s.id for s in db.query(models.Storyboard.id).filter(models.Storyboard.owner_id == current_user.id).all()]
    job_ids = [j.id for j in db.query(models.RenderJob.id).filter(models.RenderJob.user_id == current_user.id).all()]
    
    return db.query(models.Subtitle).filter(
        (models.Subtitle.storyboard_id.in_(sb_ids)) | (models.Subtitle.render_job_id.in_(job_ids))
    ).offset(skip).limit(limit).all()

@app.post(f"{settings.API_V1_STR}/audio/subtitles", response_model=schemas.SubtitleResponse, status_code=status.HTTP_201_CREATED)
def create_subtitle(
    sub_in: schemas.SubtitleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Verify ownership of destination storyboard/render_job
    if sub_in.storyboard_id:
        sb = db.query(models.Storyboard).filter(
            models.Storyboard.id == sub_in.storyboard_id,
            models.Storyboard.owner_id == current_user.id
        ).first()
        if not sb:
            raise HTTPException(status_code=403, detail="Not authorized to add subtitles to this storyboard")
    if sub_in.render_job_id:
        job = db.query(models.RenderJob).filter(
            models.RenderJob.id == sub_in.render_job_id,
            models.RenderJob.user_id == current_user.id
        ).first()
        if not job:
            raise HTTPException(status_code=403, detail="Not authorized to add subtitles to this render job")

    sub = models.Subtitle(**sub_in.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

@app.delete(f"{settings.API_V1_STR}/audio/subtitles/{{sub_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subtitle(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    sub = db.query(models.Subtitle).filter(models.Subtitle.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subtitle not found")
        
    if sub.storyboard_id:
        sb = db.query(models.Storyboard).filter(
            models.Storyboard.id == sub.storyboard_id,
            models.Storyboard.owner_id == current_user.id
        ).first()
        if not sb:
            raise HTTPException(status_code=403, detail="Not authorized to edit this storyboard's subtitles")
    elif sub.render_job_id:
        job = db.query(models.RenderJob).filter(
            models.RenderJob.id == sub.render_job_id,
            models.RenderJob.user_id == current_user.id
        ).first()
        if not job:
            raise HTTPException(status_code=403, detail="Not authorized to edit this render job's subtitles")
            
    db.delete(sub)
    db.commit()
    return None

# --- MLOPS ENDPOINTS ---

@app.post(f"{settings.API_V1_STR}/mlops/datasets", response_model=schemas.DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    dataset_in: schemas.DatasetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    dataset = models.Dataset(
        name=dataset_in.name,
        storage_path=dataset_in.storage_path,
        owner_id=current_user.id
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset

@app.get(f"{settings.API_V1_STR}/mlops/datasets", response_model=List[schemas.DatasetResponse])
def list_datasets(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.Dataset).filter(models.Dataset.owner_id == current_user.id).offset(skip).limit(limit).all()

@app.post(f"{settings.API_V1_STR}/mlops/train", response_model=schemas.FineTuningJobResponse, status_code=status.HTTP_201_CREATED)
def trigger_fine_tuning(
    job_in: schemas.FineTuningJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Verify dataset ownership
    dataset = db.query(models.Dataset).filter(
        models.Dataset.id == job_in.dataset_id,
        models.Dataset.owner_id == current_user.id
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    job = models.FineTuningJob(
        model_name=job_in.model_name,
        epochs=job_in.epochs,
        learning_rate=job_in.learning_rate,
        dataset_id=job_in.dataset_id,
        owner_id=current_user.id,
        status="PENDING",
        progress=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch to Celery — fallback to FastAPI BackgroundTasks if broker (Redis) is unavailable
    try:
        tasks.run_fine_tuning_task.delay(job.id)
    except Exception as e:
        logger.warning(f"Celery broker unavailable — falling back to FastAPI BackgroundTasks for fine-tuning job {job.id}: {e}")
        background_tasks.add_task(tasks.run_fine_tuning_task, job.id)

    return job

@app.get(f"{settings.API_V1_STR}/mlops/train", response_model=List[schemas.FineTuningJobResponse])
def list_fine_tuning_jobs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.FineTuningJob).filter(models.FineTuningJob.owner_id == current_user.id).offset(skip).limit(limit).all()

@app.get(f"{settings.API_V1_STR}/mlops/models", response_model=List[schemas.ModelVersionResponse])
def list_model_registry_versions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.ModelVersion).offset(skip).limit(limit).all()

# --- SAAS ENTERPRISE ENDPOINTS ---

@app.post(f"{settings.API_V1_STR}/saas/billing/checkout")
def create_billing_checkout(
    request: schemas.BillingCheckoutRequest,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    from app.services.billing_manager import BillingManager
    checkout_url = BillingManager.create_checkout_session(current_user.id, request.plan)
    return {"checkout_url": checkout_url}

@app.post(f"{settings.API_V1_STR}/saas/billing/webhook")
def mock_billing_webhook(
    user_id: int,
    amount: int,
    secret: Optional[str] = None,
    x_webhook_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # Verify signature/secret for security check
    if secret != settings.SECRET_KEY and x_webhook_secret != settings.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized webhook call")
    from app.services.billing_manager import BillingManager
    tx = BillingManager.process_credits_transaction(
        db=db,
        user_id=user_id,
        amount=amount,
        transaction_type="purchase",
        description="Stripe payment token deposit"
    )
    return {"status": "success", "transaction_id": tx.id}

@app.get(f"{settings.API_V1_STR}/saas/billing/transactions", response_model=List[schemas.CreditTransactionResponse])
def list_credit_transactions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.CreditTransaction).filter(models.CreditTransaction.user_id == current_user.id).offset(skip).limit(limit).all()

@app.post(f"{settings.API_V1_STR}/saas/teams", response_model=schemas.TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team_workspace(
    team_in: schemas.TeamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    team = models.Team(name=team_in.name, owner_id=current_user.id)
    db.add(team)
    db.commit()
    db.refresh(team)

    # Automatically add owner as Owner team member
    member = models.TeamMember(team_id=team.id, user_id=current_user.id, role="owner")
    db.add(member)
    db.commit()
    return team

@app.get(f"{settings.API_V1_STR}/saas/teams", response_model=List[schemas.TeamResponse])
def list_team_workspaces(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Retrieve all teams where user is member
    return db.query(models.Team).join(models.TeamMember).filter(models.TeamMember.user_id == current_user.id).offset(skip).limit(limit).all()

@app.post(f"{settings.API_V1_STR}/saas/apikeys", response_model=schemas.ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    key_in: schemas.ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    import secrets
    import hashlib
    raw_key = f"ath_{secrets.token_hex(24)}"
    h = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix = raw_key[:12]
    
    key = models.ApiKey(
        name=key_in.name,
        key_hash=h,
        key_prefix=prefix,
        user_id=current_user.id
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    
    # Return custom response with the raw key so it is shown once
    return schemas.ApiKeyCreatedResponse(
        id=key.id,
        name=key.name,
        raw_key=raw_key,
        key_prefix=prefix,
        user_id=key.user_id,
        created_at=key.created_at
    )

@app.get(f"{settings.API_V1_STR}/saas/apikeys", response_model=List[schemas.ApiKeyResponse])
def list_api_keys(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return db.query(models.ApiKey).filter(models.ApiKey.user_id == current_user.id).offset(skip).limit(limit).all()

# --- AI COPILOT ENDPOINTS ---

@app.post(f"{settings.API_V1_STR}/copilot/chat")
def get_copilot_advice(
    request: schemas.CopilotChatRequest,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    from app.services.copilot_service import CopilotService
    return CopilotService.generate_prompt_guidance(request.prompt)

@app.post(f"{settings.API_V1_STR}/copilot/estimate")
def get_render_estimate(
    request: schemas.CopilotEstimateRequest,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    from app.services.copilot_service import CopilotService
    return CopilotService.estimate_rendering_cost(request.duration, request.steps)
