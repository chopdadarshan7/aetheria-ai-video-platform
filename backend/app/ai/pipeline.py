import io
import time
import random
import logging
from typing import Dict, Any, Optional, Callable, List
from PIL import Image

try:
    import numpy as np
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from .model_manager import ModelManager
from .prompt_engine import PromptEngine
from ..services.storage_manager import StorageManager

logger = logging.getLogger(__name__)

class AIPipeline:
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager

    @staticmethod
    def compile_frames_to_mp4(frames: List[Image.Image], fps: int = 8) -> bytes:
        """Convert a list of PIL Images into an MP4 binary byte stream."""
        if not frames:
            return b""

        # Fallback to simple bytes buffer if OpenCV is not installed
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not installed. Compiling video with mock binary buffer fallback.")
            # Standard mock video format indicator
            return b"MOCK_MP4_FORMAT_DATA_STREAM"

        try:
            # Get video dimensions from first frame
            width, height = frames[0].size
            
            # Temporary file write
            import tempfile
            import os
            
            fd, temp_path = tempfile.mkstemp(suffix=".mp4")
            try:
                # Use mp4v codec for cross-platform compatibility
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
                
                for frame in frames:
                    # Convert PIL RGB to OpenCV BGR representation
                    open_cv_image = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
                    out.write(open_cv_image)
                out.release()
                
                # Read file bytes
                with open(temp_path, "rb") as f:
                    video_bytes = f.read()
            finally:
                os.close(fd)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return video_bytes
        except Exception as e:
            logger.error(f"Error compiling frames to video file: {e}", exc_info=True)
            return b"FAILED_TO_COMPILE_VIDEO_STREAM"

    def run_generation(
        self,
        job_id: int,
        job_type: str,
        prompt: str,
        negative_prompt: Optional[str] = None,
        aspect_ratio: str = "16:9",
        duration: int = 5,
        steps: int = 25,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None,
        motion_strength: int = 127,
        input_image: Optional[Image.Image] = None,
        mask_image: Optional[Image.Image] = None,
        fps: int = 8,
        model_version: Optional[str] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate the modular AI video generation pipeline:
        1. Parse & Enhance Prompt (10%)
        2. Load model (25%)
        3. Run inference (diffusers) (80%)
        4. Compile MP4 (90%)
        5. Upload bundle (GIF, metadata, thumbs) (100%)
        """
        start_time = time.time()
        
        # Initialize Seed
        if seed is None:
            seed = random.randint(0, 999999999)
            
        def report_progress(percent: int):
            if progress_callback:
                try:
                    progress_callback(percent)
                except Exception as ex:
                    logger.warning(f"Failed triggering progress callback: {ex}")

        # Stage 1: Prompt Parsing & Enhancement
        report_progress(5)
        logger.info(f"Pipeline: Processing prompts for job {job_id}...")
        enhanced_prompt, parsed_negative = PromptEngine.enhance_prompt(prompt)
        
        # Override negative prompt if provided by user
        final_negative = negative_prompt or parsed_negative
        report_progress(10)

        # Stage 2: Load relevant model
        model_id = model_version or ("svd-xt" if job_type == "image-to-video" else "cogvideox-2b")
        logger.info(f"Pipeline: Loading model '{model_id}'...")
        pipeline = self.model_manager.load_model(model_id)
        report_progress(25)

        # Stage 3: Diffusion Inference
        logger.info(f"Pipeline: Executing diffusion inference model '{model_id}' (seed: {seed})...")
        
        # Setup mock/real execution context
        inference_steps = 4
        frames: List[Image.Image] = []
        
        try:
            # Check if this is the fallback mock pipeline
            from .model_manager import MockPipeline
            if isinstance(pipeline, MockPipeline):
                # Simulate loading and execution ticks
                for i in range(inference_steps):
                    time.sleep(1.0)
                    percent = 25 + int(((i + 1) / inference_steps) * 55) # scale 25% -> 80%
                    report_progress(percent)
                
                # Fetch mock frames
                output = pipeline()
                frames = output.frames
            else:
                # Real GPU execution
                import torch
                generator = torch.manual_seed(seed)
                if torch.cuda.is_available():
                    generator = torch.Generator(device="cuda").manual_seed(seed)
                
                def diffusers_callback(step: int, timestep: int, latents: Any):
                    percent = 25 + int((step / steps) * 55)
                    report_progress(percent)

                num_frames = fps * duration

                if model_id == "controlnet-canny":
                    if not input_image:
                        raise ValueError("ControlNet Canny requires a reference image.")
                    
                    # Convert to numpy array and detect edges
                    image_np = np.array(input_image)
                    canny_img = cv2.Canny(image_np, 100, 200)
                    canny_img = canny_img[:, :, None]
                    canny_img = np.concatenate([canny_img, canny_img, canny_img], axis=2)
                    canny_pil = Image.fromarray(canny_img)
                    
                    # Generate frame sequences
                    for f_idx in range(num_frames):
                        single_out = pipeline(
                            prompt=enhanced_prompt,
                            image=canny_pil,
                            num_inference_steps=steps,
                            guidance_scale=cfg_scale,
                            generator=generator
                        )
                        frames.append(single_out.images[0])
                        percent = 25 + int((f_idx / num_frames) * 55)
                        report_progress(percent)

                elif model_id == "sd-inpainting":
                    if not input_image:
                        raise ValueError("Inpainting requires a base input reference image.")
                    
                    # Generate simple mask if not provided
                    if not mask_image:
                        mask_image = Image.new("L", input_image.size, color=0)
                        from PIL import ImageDraw
                        draw = ImageDraw.Draw(mask_image)
                        w, h = input_image.size
                        draw.rectangle([w//4, h//4, 3*w//4, 3*h//4], fill=255)
                    
                    # Generate frame sequences
                    for f_idx in range(num_frames):
                        single_out = pipeline(
                            prompt=enhanced_prompt,
                            image=input_image,
                            mask_image=mask_image,
                            num_inference_steps=steps,
                            guidance_scale=cfg_scale,
                            generator=generator
                        )
                        frames.append(single_out.images[0])
                        percent = 25 + int((f_idx / num_frames) * 55)
                        report_progress(percent)

                elif job_type == "image-to-video":
                    if not input_image:
                        raise ValueError("Image-to-Video requires an input reference image.")
                    
                    if input_image.mode != "RGB":
                        input_image = input_image.convert("RGB")
                    
                    output = pipeline(
                        input_image,
                        height=288,
                        width=512,
                        num_frames=num_frames,
                        motion_bucket_id=motion_strength,
                        noise_aug_strength=0.1,
                        generator=generator,
                        callback=diffusers_callback,
                        callback_steps=1
                    )
                    frames = output.frames
                else: # Text-to-Video
                    output = pipeline(
                        enhanced_prompt,
                        height=288,
                        width=512,
                        num_frames=num_frames,
                        num_inference_steps=steps,
                        guidance_scale=cfg_scale,
                        generator=generator,
                        callback=diffusers_callback,
                        callback_steps=1
                    )
                    frames = output.frames
                
        except Exception as inf_err:
            logger.error(f"Inference error in pipeline execution: {inf_err}", exc_info=True)
            raise inf_err

        report_progress(80)

        # Stage 4: Compile frames to MP4 video format
        logger.info(f"Pipeline: Compiling generated frames into MP4 video container...")
        video_bytes = self.compile_frames_to_mp4(frames, fps=fps)
        report_progress(90)

        # Stage 5: Upload generation bundle (video, thumbnails, gifs, metadata)
        inference_time_sec = round(time.time() - start_time, 2)
        logger.info(f"Pipeline: Uploading final assets bundle to S3. Duration: {inference_time_sec}s...")
        
        metadata = {
            "job_id": job_id,
            "job_type": job_type,
            "prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "negative_prompt": final_negative,
            "aspect_ratio": aspect_ratio,
            "duration": duration,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "seed": seed,
            "motion_strength": motion_strength,
            "fps": fps,
            "resolution": f"{frames[0].width}x{frames[0].height}" if frames else "512x288",
            "inference_time_seconds": inference_time_sec,
            "model_version": model_id
        }
        
        video_url, thumb_url, gif_url, meta_url = StorageManager.upload_generation_bundle(
            job_id=job_id,
            video_bytes=video_bytes,
            frames=frames,
            params=metadata
        )
        
        report_progress(100)
        
        return {
            "video_url": video_url,
            "thumbnail_url": thumb_url,
            "gif_url": gif_url,
            "metadata_url": meta_url,
            "metadata": metadata
        }
