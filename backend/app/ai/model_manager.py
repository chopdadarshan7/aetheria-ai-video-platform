import os
import logging
from typing import Dict, Any, Optional
from .gpu_manager import GPUManager

try:
    import torch
    from diffusers import (
        StableVideoDiffusionPipeline,
        CogVideoXPipeline,
        DiffusionPipeline,
        StableDiffusionControlNetPipeline,
        StableDiffusionInpaintPipeline,
        ControlNetModel
    )
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Model Registry Database
MODEL_REGISTRY = {
    "svd-xt": {
        "repo_id": "stabilityai/stable-video-diffusion-img2vid-xt",
        "description": "Stable Video Diffusion XT for high quality Image-to-Video generation",
        "type": "image-to-video",
        "class": "StableVideoDiffusionPipeline"
    },
    "cogvideox-2b": {
        "repo_id": "THUDM/CogVideoX-2b",
        "description": "CogVideoX-2b for efficient Text-to-Video generation",
        "type": "text-to-video",
        "class": "CogVideoXPipeline"
    },
    "ltx-video": {
        "repo_id": "Lightricks/LTX-Video",
        "description": "LTX-Video transformer pipeline for Text-to-Video & Image-to-Video",
        "type": "text-to-video",
        "class": "DiffusionPipeline"
    },
    "controlnet-canny": {
        "repo_id": "lllyasviel/sd-controlnet-canny",
        "description": "ControlNet Canny Edge boundary mapping for structured video conditioning",
        "type": "controlnet",
        "class": "StableDiffusionControlNetPipeline"
    },
    "sd-inpainting": {
        "repo_id": "runwayml/stable-diffusion-inpainting",
        "description": "Stable Diffusion Inpainting for local modifications and scene outpaint extensions",
        "type": "inpainting",
        "class": "StableDiffusionInpaintPipeline"
    }
}

class MockPipeline:
    """Mock pipeline fallback class for environments without GPU support."""
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        logger.info(f"Initialized MockPipeline for model repository: {repo_id}")

    def __call__(self, *args, **kwargs):
        # Return mock outputs matching standard structure (PIL images or lists of images)
        logger.info(f"Mock pipeline call triggered for {self.repo_id}")
        from PIL import Image
        
        # Create dummy frame sequence (e.g. 8 black images with text)
        frames = []
        for i in range(8):
            img = Image.new("RGB", (512, 288), color=(i * 20, 20, 50))
            frames.append(img)
            
        class MockOutput:
            def __init__(self, frames):
                self.frames = frames
        return MockOutput(frames)

    def to(self, device):
        logger.info(f"Mock pipeline moved to device: {device}")
        return self

    def enable_model_cpu_offload(self):
        logger.info("Mock pipeline: model CPU offload enabled")

    def enable_sequential_cpu_offload(self):
        logger.info("Mock pipeline: sequential CPU offload enabled")

    def enable_attention_slicing(self):
        logger.info("Mock pipeline: attention slicing enabled")

    def enable_vae_slicing(self):
        logger.info("Mock pipeline: VAE slicing enabled")


class ModelManager:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.getenv("HF_HOME", "./model_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Store for active loaded model pipelines
        self.loaded_pipelines: Dict[str, Any] = {}
        self.active_model_id: Optional[str] = None
        logger.info(f"ModelManager initialized. Caching in: {self.cache_dir}")

    def list_models(self) -> dict:
        """Returns the registered models details along with loaded status."""
        models_list = {}
        for mid, details in MODEL_REGISTRY.items():
            models_list[mid] = {
                **details,
                "loaded": mid in self.loaded_pipelines,
                "active": mid == self.active_model_id,
                "cached": os.path.exists(os.path.join(self.cache_dir, f"hub/models--{details['repo_id'].replace('/', '--')}"))
            }
        return models_list

    def load_model(self, model_id: str, precision: str = "fp16", optimize_vram: bool = True) -> Any:
        """Dynamically load model pipeline from cache/Hugging Face, applying VRAM optimizations."""
        if model_id not in MODEL_REGISTRY:
            raise ValueError(f"Model ID '{model_id}' is not registered.")

        # Check if already loaded
        if model_id in self.loaded_pipelines:
            logger.info(f"Model '{model_id}' is already loaded in memory.")
            self.active_model_id = model_id
            return self.loaded_pipelines[model_id]

        # Unload active model to conserve GPU VRAM if loading a new one
        if self.active_model_id and self.active_model_id != model_id:
            self.unload_model(self.active_model_id)

        model_info = MODEL_REGISTRY[model_id]
        repo_id = model_info["repo_id"]
        pipeline_class_name = model_info["class"]
        
        device = GPUManager.get_optimal_device()
        logger.info(f"Loading model '{model_id}' ({repo_id}) on device: {device}...")

        # If GPU/Diffusers are not available, fallback to mock pipeline
        if not DIFFUSERS_AVAILABLE or device == "cpu":
            logger.warning("GPU or Hugging Face diffusers module not fully configured. Using fallback MockPipeline.")
            pipeline = MockPipeline(repo_id)
            self.loaded_pipelines[model_id] = pipeline
            self.active_model_id = model_id
            return pipeline

        # Map pipeline strings to class references
        try:
            torch_dtype = torch.float16 if precision == "fp16" else torch.float32
            if precision == "bf16" and hasattr(torch, "bfloat16"):
                torch_dtype = torch.bfloat16
                
            if model_id == "controlnet-canny":
                controlnet = ControlNetModel.from_pretrained(
                    repo_id,
                    torch_dtype=torch_dtype,
                    cache_dir=self.cache_dir
                )
                pipeline = StableDiffusionControlNetPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    controlnet=controlnet,
                    torch_dtype=torch_dtype,
                    cache_dir=self.cache_dir
                )
            elif model_id == "sd-inpainting":
                pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                    repo_id,
                    torch_dtype=torch_dtype,
                    cache_dir=self.cache_dir
                )
            else:
                pipeline_cls = globals().get(pipeline_class_name, DiffusionPipeline)
                pipeline = pipeline_cls.from_pretrained(
                    repo_id,
                    torch_dtype=torch_dtype,
                    cache_dir=self.cache_dir,
                    variant="fp16" if precision == "fp16" else None,
                    use_safetensors=True
                )
            
            # Move to target device
            pipeline.to(device)

            # Apply VRAM optimization techniques if requested and running on CUDA
            if optimize_vram and device == "cuda":
                logger.info(f"Applying GPU memory optimizations to '{model_id}'...")
                
                # Model CPU offloading (offloads components to host memory when not active)
                try:
                    pipeline.enable_model_cpu_offload()
                except AttributeError:
                    pass

                # VAE Slicing (splits large frame batches during decoding)
                try:
                    pipeline.enable_vae_slicing()
                except AttributeError:
                    pass
                    
                # Attention Slicing
                try:
                    pipeline.enable_attention_slicing()
                except AttributeError:
                    pass

            self.loaded_pipelines[model_id] = pipeline
            self.active_model_id = model_id
            logger.info(f"Successfully loaded model: {model_id}")
            return pipeline

        except Exception as e:
            logger.error(f"Failed loading model pipeline for {repo_id}: {e}", exc_info=True)
            raise RuntimeError(f"Error loading model {model_id}: {e}")

    def unload_model(self, model_id: str) -> None:
        """Unload pipeline from RAM/VRAM to free up system memory resources."""
        if model_id in self.loaded_pipelines:
            del self.loaded_pipelines[model_id]
            if self.active_model_id == model_id:
                self.active_model_id = None
            GPUManager.cleanup_memory()
            logger.info(f"Unloaded model pipeline: {model_id}")

    def switch_active_model(self, model_id: str) -> Any:
        """Switch active loaded model, loading if not already in memory."""
        return self.load_model(model_id)

    def delete_cached_files(self, model_id: str) -> bool:
        """Remove model binary files from the local storage cache directory."""
        if model_id not in MODEL_REGISTRY:
            return False
            
        model_info = MODEL_REGISTRY[model_id]
        repo_id = model_info["repo_id"]
        # Hugging Face caches names by repo ID with double dashes
        folder_name = f"models--{repo_id.replace('/', '--')}"
        folder_path = os.path.join(self.cache_dir, "hub", folder_name)
        
        # If currently loaded, unload it first
        self.unload_model(model_id)
        
        if os.path.exists(folder_path):
            import shutil
            shutil.rmtree(folder_path)
            logger.info(f"Deleted cache files for model: {model_id} at {folder_path}")
            return True
        logger.info(f"No cache folders found for model: {model_id}")
        return False
