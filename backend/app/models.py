import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    credits = Column(Float, default=100.0)  # Initial credits given to users
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="owner", cascade="all, delete-orphan")
    render_jobs = relationship("RenderJob", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="projects")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    render_jobs = relationship("RenderJob", back_populates="project", cascade="all, delete-orphan")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String, nullable=False)  # S3 Key or local storage path
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="assets")
    project = relationship("Project", back_populates="assets")

class RenderJob(Base):
    __tablename__ = "render_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String, nullable=False)  # "text-to-video", "image-to-video", etc.
    status = Column(String, default="PENDING")  # PENDING, RUNNING, SUCCESS, FAILED, CANCELLED
    progress = Column(Integer, default=0)       # 0 to 100
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    aspect_ratio = Column(String, default="16:9")
    duration = Column(Integer, default=5)       # Target duration in seconds
    cost = Column(Float, default=10.0)          # Credit cost
    
    # Generation Parameters
    steps = Column(Integer, default=25)
    cfg_scale = Column(Float, default=7.5)
    seed = Column(Integer, nullable=True)
    motion_strength = Column(Integer, default=127)
    fps = Column(Integer, default=8)
    model_version = Column(String, default="svd-xt")

    # Input files if any (e.g. image-to-video image file)
    input_asset_id = Column(Integer, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    
    # Results
    result_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    gif_url = Column(String, nullable=True)
    metadata_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    user = relationship("User", back_populates="render_jobs")
    project = relationship("Project", back_populates="render_jobs")
    input_asset = relationship("Asset", foreign_keys=[input_asset_id])

class Storyboard(Base):
    __tablename__ = "storyboards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    
    # Progress tracking attributes
    status = Column(String, default="PENDING")  # PENDING, RUNNING, SUCCESS, FAILED
    progress = Column(Integer, default=0)
    result_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    scenes = relationship("Scene", back_populates="storyboard", cascade="all, delete-orphan")
    timeline = relationship("Timeline", back_populates="storyboard", uselist=False, cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    order = Column(Integer, default=0)
    storyboard_id = Column(Integer, ForeignKey("storyboards.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    storyboard = relationship("Storyboard", back_populates="scenes")
    shots = relationship("Shot", back_populates="scene", cascade="all, delete-orphan")

class Shot(Base):
    __tablename__ = "shots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    order = Column(Integer, default=0)
    scene_id = Column(Integer, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    
    # Generation parameters
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    aspect_ratio = Column(String, default="16:9")
    duration = Column(Integer, default=5)
    steps = Column(Integer, default=25)
    cfg_scale = Column(Float, default=7.5)
    seed = Column(Integer, nullable=True)
    motion_strength = Column(Integer, default=127)
    fps = Column(Integer, default=8)
    model_version = Column(String, default="cogvideox-2b")
    
    # Motion and camera paths settings (JSON strings)
    camera_path = Column(Text, nullable=True)
    motion_brush = Column(Text, nullable=True)
    
    # Associated RenderJob
    render_job_id = Column(Integer, ForeignKey("render_jobs.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    scene = relationship("Scene", back_populates="shots")
    render_job = relationship("RenderJob", foreign_keys=[render_job_id])

class Timeline(Base):
    __tablename__ = "timelines"

    id = Column(Integer, primary_key=True, index=True)
    storyboard_id = Column(Integer, ForeignKey("storyboards.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    storyboard = relationship("Storyboard", back_populates="timeline")
    layers = relationship("Layer", back_populates="timeline", cascade="all, delete-orphan")

class Layer(Base):
    __tablename__ = "layers"

    id = Column(Integer, primary_key=True, index=True)
    timeline_id = Column(Integer, ForeignKey("timelines.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    order = Column(Integer, default=0)
    layer_type = Column(String, default="video")

    # Relationships
    timeline = relationship("Timeline", back_populates="layers")
    items = relationship("TimelineItem", back_populates="layer", cascade="all, delete-orphan")

class TimelineItem(Base):
    __tablename__ = "timeline_items"

    id = Column(Integer, primary_key=True, index=True)
    layer_id = Column(Integer, ForeignKey("layers.id", ondelete="CASCADE"), nullable=False)
    
    # References to Shot or Asset
    shot_id = Column(Integer, ForeignKey("shots.id", ondelete="SET NULL"), nullable=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    
    start_time = Column(Float, default=0.0)
    duration = Column(Float, default=5.0)
    
    # Transitions
    transition_in = Column(String, nullable=True)
    transition_out = Column(String, nullable=True)

    # Relationships
    layer = relationship("Layer", back_populates="items")
    shot = relationship("Shot", foreign_keys=[shot_id])
    asset = relationship("Asset", foreign_keys=[asset_id])

class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    language = Column(String, default="en")
    embedding_path = Column(String, nullable=True) # S3 or local path to cloned embeddings
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class Subtitle(Base):
    __tablename__ = "subtitles"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    start_time = Column(Float, default=0.0)
    end_time = Column(Float, default=5.0)
    storyboard_id = Column(Integer, ForeignKey("storyboards.id", ondelete="CASCADE"), nullable=True)
    render_job_id = Column(Integer, ForeignKey("render_jobs.id", ondelete="CASCADE"), nullable=True)

class AudioJob(Base):
    __tablename__ = "audio_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String, nullable=False) # tts, stt, cloning, music, sound-fx, dubbing, lip-sync
    status = Column(String, default="PENDING")
    progress = Column(Integer, default=0)
    prompt = Column(Text, nullable=True)
    
    # Associated configs
    voice_profile_id = Column(Integer, ForeignKey("voice_profiles.id", ondelete="SET NULL"), nullable=True)
    
    # Output file
    result_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    storage_path = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, VALIDATED, FAILED
    auto_captions = Column(Text, nullable=True) # stringified JSON
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class FineTuningJob(Base):
    __tablename__ = "fine_tuning_jobs"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True, nullable=False)
    status = Column(String, default="PENDING")
    progress = Column(Integer, default=0)
    epochs = Column(Integer, default=10)
    learning_rate = Column(Float, default=1e-4)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    result_model_path = Column(String, nullable=True)
    metrics = Column(Text, nullable=True) # stringified metrics history dict
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    version = Column(String, nullable=False)
    path = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    stripe_subscription_id = Column(String, index=True, nullable=True)
    stripe_customer_id = Column(String, index=True, nullable=True)
    plan_name = Column(String, default="free") # free, creator, enterprise
    status = Column(String, default="active") # active, cancelled, incomplete
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=True)

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String, nullable=False) # purchase, usage, refund
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, default="member") # owner, admin, member

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    key_prefix = Column(String, nullable=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
