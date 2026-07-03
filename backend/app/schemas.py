from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Generic response
class MessageResponse(BaseModel):
    status: str
    message: str

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    credits: float
    is_active: bool
    is_admin: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class UserCreditsUpdate(BaseModel):
    credits: float

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Asset Schemas
class AssetResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    mime_type: str
    file_size: int
    storage_path: str
    owner_id: int
    project_id: Optional[int]
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Render Job Schemas
class RenderJobCreate(BaseModel):
    job_type: str = Field(..., description="e.g. text-to-video, image-to-video")
    prompt: str
    negative_prompt: Optional[str] = None
    aspect_ratio: str = "16:9"
    duration: int = 5
    steps: int = 25
    cfg_scale: float = 7.5
    seed: Optional[int] = None
    motion_strength: int = 127
    fps: int = 8
    model_version: str = "svd-xt"
    project_id: Optional[int] = None
    input_asset_id: Optional[int] = None

class RenderJobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    progress: int
    prompt: str
    negative_prompt: Optional[str]
    aspect_ratio: str
    duration: int
    cost: float
    steps: int
    cfg_scale: float
    seed: Optional[int]
    motion_strength: int
    fps: int
    model_version: Optional[str]
    input_asset_id: Optional[int]
    result_url: Optional[str]
    thumbnail_url: Optional[str]
    gif_url: Optional[str]
    metadata_url: Optional[str]
    error_message: Optional[str]
    user_id: int
    project_id: Optional[int]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Model Management Schemas
class ModelInfo(BaseModel):
    id: str
    repo_id: str
    description: str
    type: str
    loaded: bool
    active: bool
    cached: bool

class ModelSwitchRequest(BaseModel):
    model_id: str

# Prompt Understanding Schema
class PromptStructured(BaseModel):
    subject: str
    action: str
    location: str
    lighting: str
    camera: str
    style: str
    weather: str
    emotion: str

# --- NEW: Proper request body schemas (replaces bare query params) ---

class PromptEnhanceRequest(BaseModel):
    """Request body for POST /prompt/enhance"""
    prompt: str = Field(..., min_length=1, max_length=2000)

class CopilotChatRequest(BaseModel):
    """Request body for POST /copilot/chat"""
    prompt: str = Field(..., min_length=1, max_length=2000)

class CopilotEstimateRequest(BaseModel):
    """Request body for POST /copilot/estimate"""
    duration: float = Field(..., gt=0, le=300)
    steps: int = Field(..., ge=1, le=200)

class BillingCheckoutRequest(BaseModel):
    """Request body for POST /saas/billing/checkout"""
    plan: str = Field(..., description="Plan name: free, creator, enterprise")

# Storyboard & Timeline Editor Schemas
class ShotBase(BaseModel):
    name: str
    order: Optional[int] = 0
    prompt: str
    negative_prompt: Optional[str] = None
    aspect_ratio: Optional[str] = "16:9"
    duration: Optional[int] = 5
    steps: Optional[int] = 25
    cfg_scale: Optional[float] = 7.5
    seed: Optional[int] = None
    motion_strength: Optional[int] = 127
    fps: Optional[int] = 8
    model_version: Optional[str] = "cogvideox-2b"
    camera_path: Optional[str] = None
    motion_brush: Optional[str] = None

class ShotCreate(ShotBase):
    pass

class ShotResponse(ShotBase):
    id: int
    scene_id: int
    render_job_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class SceneBase(BaseModel):
    name: str
    order: Optional[int] = 0

class SceneCreate(SceneBase):
    pass

class SceneResponse(SceneBase):
    id: int
    storyboard_id: int
    shots: List[ShotResponse] = []

    model_config = ConfigDict(from_attributes=True)

class TimelineItemBase(BaseModel):
    shot_id: Optional[int] = None
    asset_id: Optional[int] = None
    start_time: float = 0.0
    duration: float = 5.0
    transition_in: Optional[str] = None
    transition_out: Optional[str] = None

class TimelineItemCreate(TimelineItemBase):
    pass

class TimelineItemResponse(TimelineItemBase):
    id: int
    layer_id: int

    model_config = ConfigDict(from_attributes=True)

class LayerBase(BaseModel):
    name: str
    order: Optional[int] = 0
    layer_type: str = "video"

class LayerCreate(LayerBase):
    pass

class LayerResponse(LayerBase):
    id: int
    timeline_id: int
    items: List[TimelineItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

class TimelineResponse(BaseModel):
    id: int
    storyboard_id: int
    layers: List[LayerResponse] = []

    model_config = ConfigDict(from_attributes=True)

class StoryboardBase(BaseModel):
    name: str
    description: Optional[str] = None

class StoryboardCreate(StoryboardBase):
    project_id: Optional[int] = None

class StoryboardResponse(StoryboardBase):
    id: int
    owner_id: int
    project_id: Optional[int]
    status: str
    progress: int
    result_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    scenes: List[SceneResponse] = []
    timeline: Optional[TimelineResponse] = None

    model_config = ConfigDict(from_attributes=True)

# --- AUDIO INTELLIGENCE SCHEMAS ---
class VoiceProfileBase(BaseModel):
    name: str
    language: Optional[str] = "en"

class VoiceProfileCreate(VoiceProfileBase):
    pass

class VoiceProfileResponse(VoiceProfileBase):
    id: int
    embedding_path: Optional[str]
    owner_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class SubtitleBase(BaseModel):
    text: str
    start_time: float
    end_time: float

class SubtitleCreate(SubtitleBase):
    storyboard_id: Optional[int] = None
    render_job_id: Optional[int] = None

class SubtitleResponse(SubtitleBase):
    id: int
    storyboard_id: Optional[int]
    render_job_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)

class AudioJobBase(BaseModel):
    job_type: str
    prompt: Optional[str] = None
    voice_profile_id: Optional[int] = None

class AudioJobCreate(AudioJobBase):
    pass

class AudioJobResponse(AudioJobBase):
    id: int
    status: str
    progress: int
    result_url: Optional[str]
    error_message: Optional[str]
    user_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# --- MLOPS SCHEMAS ---
class DatasetBase(BaseModel):
    name: str

class DatasetCreate(DatasetBase):
    storage_path: str

class DatasetResponse(DatasetBase):
    id: int
    storage_path: str
    status: str
    auto_captions: Optional[str]
    owner_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class FineTuningJobBase(BaseModel):
    model_name: str
    epochs: Optional[int] = 10
    learning_rate: Optional[float] = 1e-4
    dataset_id: int

class FineTuningJobCreate(FineTuningJobBase):
    pass

class FineTuningJobResponse(FineTuningJobBase):
    id: int
    status: str
    progress: int
    result_model_path: Optional[str]
    metrics: Optional[str]
    owner_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class ModelVersionBase(BaseModel):
    name: str
    version: str
    path: str
    active: Optional[bool] = True

class ModelVersionResponse(ModelVersionBase):
    id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# --- ENTERPRISE SAAS SCHEMAS ---
class SubscriptionBase(BaseModel):
    plan_name: str
    status: str

class SubscriptionResponse(SubscriptionBase):
    id: int
    stripe_subscription_id: Optional[str]
    stripe_customer_id: Optional[str]
    user_id: int
    expires_at: Optional[datetime.datetime]

    model_config = ConfigDict(from_attributes=True)

class CreditTransactionBase(BaseModel):
    amount: int
    transaction_type: str
    description: Optional[str] = None

class CreditTransactionResponse(CreditTransactionBase):
    id: int
    user_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    pass

class TeamResponse(TeamBase):
    id: int
    owner_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class TeamMemberBase(BaseModel):
    team_id: int
    user_id: int
    role: Optional[str] = "member"

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberResponse(TeamMemberBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ApiKeyBase(BaseModel):
    name: str

class ApiKeyCreate(ApiKeyBase):
    pass

class ApiKeyResponse(ApiKeyBase):
    id: int
    # key_prefix shows first 8 chars only — never expose full key after creation
    key_prefix: Optional[str] = None
    user_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class ApiKeyCreatedResponse(ApiKeyBase):
    """Returned ONLY on initial creation — includes the full raw key once."""
    id: int
    raw_key: str
    key_prefix: Optional[str] = None
    user_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
