import gc
import logging

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

class GPUManager:
    @staticmethod
    def is_cuda_available() -> bool:
        if not TORCH_AVAILABLE:
            return False
        return torch.cuda.is_available()

    @staticmethod
    def get_optimal_device() -> str:
        if GPUManager.is_cuda_available():
            return "cuda"
        # Check for Apple Silicon MPS fallback
        if TORCH_AVAILABLE and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    @staticmethod
    def get_vram_info() -> dict:
        info = {"device": GPUManager.get_optimal_device(), "total_mb": 0.0, "allocated_mb": 0.0, "cached_mb": 0.0, "free_mb": 0.0}
        if not GPUManager.is_cuda_available():
            return info
        
        try:
            device_id = torch.cuda.current_device()
            total = torch.cuda.get_device_properties(device_id).total_memory
            allocated = torch.cuda.memory_allocated(device_id)
            cached = torch.cuda.memory_reserved(device_id)
            
            info.update({
                "total_mb": round(total / (1024 ** 2), 2),
                "allocated_mb": round(allocated / (1024 ** 2), 2),
                "cached_mb": round(cached / (1024 ** 2), 2),
                "free_mb": round((total - allocated) / (1024 ** 2), 2)
            })
        except Exception as e:
            logger.warning(f"Error querying VRAM status: {e}")
            
        return info

    @staticmethod
    def empty_cache() -> None:
        gc.collect()
        if GPUManager.is_cuda_available():
            torch.cuda.empty_cache()
            logger.info("Cleared CUDA GPU cache.")
        elif TORCH_AVAILABLE and hasattr(torch.cuda, "mps") and torch.backends.mps.is_available():
            # MPS doesn't have an empty_cache API but we trigger GC
            pass

    @staticmethod
    def cleanup_memory() -> None:
        """Trigger comprehensive garbage collection and flush GPU VRAM allocation pools."""
        gc.collect()
        if TORCH_AVAILABLE:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
            logger.info("Executed thorough VRAM memory cleanup.")

    @staticmethod
    def get_optimal_batch_size(width: int, height: int, duration_sec: int) -> int:
        """Estimate dynamic batch size bounds based on active VRAM properties."""
        vram = GPUManager.get_vram_info()
        free_gb = vram["free_mb"] / 1024.0
        
        if free_gb <= 0:
            return 1 # Fallback default
            
        # Estimations based on resolution parameters
        pixels = width * height
        # Very rough heuristic: standard SVD/diffusion takes more space as pixels scale
        if pixels >= (1024 * 1024): # 1080p
            if free_gb < 16.0:
                return 1
            return 2 if free_gb >= 24.0 else 1
        else: # 512x512, 768x512
            if free_gb < 8.0:
                return 1
            if free_gb < 16.0:
                return 2
            return 4
