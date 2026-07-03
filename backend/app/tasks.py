import time
import logging
import os
import json
import redis
import httpx
from celery import shared_task
from PIL import Image
import io

from .database import SessionLocal
from . import models
from .config import settings
from .ai.model_manager import ModelManager
from .ai.pipeline import AIPipeline

logger = logging.getLogger(__name__)

# Global Redis client for Pub/Sub progress broadcasting
redis_client = redis.Redis.from_url(settings.broker_url)

# Global ModelManager caching pipelines in worker process memory space
model_manager = ModelManager()
pipeline_orchestrator = AIPipeline(model_manager)

def broadcast_progress(
    user_id: int,
    job_id: int,
    progress: int,
    status: str,
    error_message: str = None,
    result_url: str = None,
    thumbnail_url: str = None,
    gif_url: str = None,
    metadata_url: str = None
):
    """Publish real-time progress update events on Redis PubSub channel."""
    payload = {
        "user_id": user_id,
        "job_id": job_id,
        "progress": progress,
        "status": status,
        "error_message": error_message,
        "result_url": result_url,
        "thumbnail_url": thumbnail_url,
        "gif_url": gif_url,
        "metadata_url": metadata_url
    }
    try:
        redis_client.publish("render_progress", json.dumps(payload))
    except Exception as e:
        logger.warning(f"Failed publishing progress to Redis: {e}")

@shared_task(name="app.tasks.enhance_prompt_task")
def enhance_prompt_task(prompt: str) -> dict:
    """Synchronous prompt parsing engine wrapper."""
    from .ai.prompt_engine import PromptEngine
    enhanced, negative = PromptEngine.enhance_prompt(prompt)
    parsed = PromptEngine.parse_prompt(prompt)
    return {
        "enhanced_prompt": enhanced,
        "negative_prompt": negative,
        **parsed
    }

@shared_task(name="app.tasks.render_video_task", bind=True)
def render_video_task(self, job_id: int):
    """
    Background rendering task:
    Downloads reference assets, runs inference through Hugging Face pipelines,
    compiles and uploads result artifacts, and broadcasts WebSockets progress.
    """
    logger.info(f"Task: Commencing render job: {job_id}")
    db = SessionLocal()
    
    # Check cancelled state early
    job = db.query(models.RenderJob).filter(models.RenderJob.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found in database.")
        return False
        
    if job.status == "CANCELLED":
        logger.info(f"Job {job_id} was pre-cancelled by user.")
        return False

    try:
        job.status = "RUNNING"
        job.progress = 5
        db.commit()
        broadcast_progress(job.user_id, job.id, 5, "RUNNING")

        # 1. Download/load input reference asset image if applicable
        input_image = None
        if job.input_asset_id:
            asset = db.query(models.Asset).filter(models.Asset.id == job.input_asset_id).first()
            if asset:
                logger.info(f"Job {job_id}: Loading reference image from path {asset.storage_path}...")
                try:
                    if asset.storage_path.startswith("http"):
                        # Read from S3 endpoint
                        res = httpx.get(asset.storage_path)
                        res.raise_for_status()
                        input_image = Image.open(io.BytesIO(res.content))
                    else:
                        # Local static file fallback
                        relative_path = asset.storage_path.lstrip("/")
                        # Map relative /static/uploads/... path
                        full_path = os.path.join("/Users/darshanchopda/Desktop/image to vieo/backend", relative_path)
                        if os.path.exists(full_path):
                            input_image = Image.open(full_path)
                        else:
                            # Direct check under static root
                            fallback_path = os.path.join("/Users/darshanchopda/Desktop/image to vieo/backend/static", relative_path.replace("static/", ""))
                            if os.path.exists(fallback_path):
                                input_image = Image.open(fallback_path)
                except Exception as img_err:
                    logger.error(f"Job {job_id}: Failed loading input asset: {img_err}", exc_info=True)
                    raise ValueError(f"Failed loading reference image: {img_err}")

        # 2. Configure progress callback handler
        def on_pipeline_progress(percent: int):
            # Fetch latest state to check cancellation
            inner_db = SessionLocal()
            try:
                inner_job = inner_db.query(models.RenderJob).filter(models.RenderJob.id == job_id).first()
                if inner_job:
                    if inner_job.status == "CANCELLED":
                        logger.info(f"Job {job_id} canceled during inference.")
                        # Force cancel raise to terminate execution
                        raise InterruptedError("Generation task was cancelled by user.")
                    
                    inner_job.progress = percent
                    inner_job.status = "RUNNING"
                    inner_db.commit()
                    broadcast_progress(inner_job.user_id, inner_job.id, percent, "RUNNING")
            finally:
                inner_db.close()

        # 3. Run Pipeline Orchestration
        result = pipeline_orchestrator.run_generation(
            job_id=job.id,
            job_type=job.job_type,
            prompt=job.prompt,
            negative_prompt=job.negative_prompt,
            aspect_ratio=job.aspect_ratio,
            duration=job.duration,
            steps=job.steps,
            cfg_scale=job.cfg_scale,
            seed=job.seed,
            motion_strength=job.motion_strength,
            input_image=input_image,
            fps=job.fps,
            progress_callback=on_pipeline_progress
        )

        # 4. Save result assets and deduct user credit balance
        job.status = "SUCCESS"
        job.progress = 100
        job.result_url = result["video_url"]
        job.thumbnail_url = result["thumbnail_url"]
        job.gif_url = result["gif_url"]
        job.metadata_url = result["metadata_url"]
        # Save exact seed resolved
        job.seed = result["metadata"]["seed"]

        user = db.query(models.User).filter(models.User.id == job.user_id).first()
        if user:
            user.credits = max(0.0, user.credits - job.cost)

        db.commit()

        # 5. Broadcast success event
        broadcast_progress(
            user_id=job.user_id,
            job_id=job.id,
            progress=100,
            status="SUCCESS",
            result_url=job.result_url,
            thumbnail_url=job.thumbnail_url,
            gif_url=job.gif_url,
            metadata_url=job.metadata_url
        )
        logger.info(f"Render job {job_id} successfully completed.")
        return True

    except InterruptedError as cancel_err:
        logger.warning(f"Job {job_id} cancelled: {cancel_err}")
        db.rollback()
        # Keep status as CANCELLED, do not override to FAILED
        job = db.query(models.RenderJob).filter(models.RenderJob.id == job_id).first()
        if job:
            job.status = "CANCELLED"
            db.commit()
            broadcast_progress(job.user_id, job.id, job.progress, "CANCELLED", error_message=str(cancel_err))
        return False

    except Exception as e:
        logger.exception(f"Error executing render job {job_id}: {e}")
        db.rollback()
        job = db.query(models.RenderJob).filter(models.RenderJob.id == job_id).first()
        if job:
            job.status = "FAILED"
            job.error_message = str(e)
            db.commit()
            broadcast_progress(job.user_id, job.id, job.progress, "FAILED", error_message=str(e))
        return False
    finally:
        db.close()

@shared_task(name="app.tasks.render_storyboard_task")
def render_storyboard_task(storyboard_id: int):
    """
    Renders all shots in a Storyboard sequentially to prevent GPU VRAM overload,
    applies configured transitions, compiles the final stitched video, and uploads it.
    """
    import tempfile
    from .services.storyboard_manager import StoryboardManager
    
    logger.info(f"Task: Starting render job for Storyboard {storyboard_id}...")
    db = SessionLocal()
    
    storyboard = db.query(models.Storyboard).filter(models.Storyboard.id == storyboard_id).first()
    if not storyboard:
        logger.error(f"Storyboard {storyboard_id} not found in database.")
        db.close()
        return False
        
    try:
        storyboard.status = "RUNNING"
        storyboard.progress = 5
        db.commit()
        
        # Helper to broadcast storyboard updates
        def broadcast_storyboard_progress(percent: int, status: str, result_url: str = None, error_message: str = None):
            payload = {
                "user_id": storyboard.owner_id,
                "storyboard_id": storyboard.id,
                "progress": percent,
                "status": status,
                "result_url": result_url,
                "error_message": error_message
            }
            try:
                redis_client.publish("render_progress", json.dumps(payload))
            except Exception as pe:
                logger.warning(f"Failed publishing storyboard progress: {pe}")

        broadcast_storyboard_progress(5, "RUNNING")
        
        # 1. Collect all scenes and shots ordered logically
        scenes = db.query(models.Scene).filter(models.Scene.storyboard_id == storyboard_id).order_by(models.Scene.order.asc()).all()
        shots_ordered = []
        for scene in scenes:
            scene_shots = db.query(models.Shot).filter(models.Shot.scene_id == scene.id).order_by(models.Shot.order.asc()).all()
            shots_ordered.extend(scene_shots)
            
        if not shots_ordered:
            raise ValueError("Storyboard contains no shots/scenes to render.")

        # 2. Render each shot sequentially
        total_shots = len(shots_ordered)
        
        for idx, shot in enumerate(shots_ordered):
            logger.info(f"Rendering Shot {idx + 1}/{total_shots}: {shot.name}...")
            
            # Retrieve or create render job
            job = None
            if shot.render_job_id:
                job = db.query(models.RenderJob).filter(models.RenderJob.id == shot.render_job_id).first()
            
            if not job:
                # Estimate cost: 10 credits flat
                job = models.RenderJob(
                    job_type="text-to-video",
                    status="PENDING",
                    progress=0,
                    prompt=shot.prompt,
                    negative_prompt=shot.negative_prompt,
                    aspect_ratio=shot.aspect_ratio,
                    duration=shot.duration,
                    cost=10.0,
                    steps=shot.steps,
                    cfg_scale=shot.cfg_scale,
                    seed=shot.seed,
                    motion_strength=shot.motion_strength,
                    fps=shot.fps,
                    model_version=shot.model_version,
                    user_id=storyboard.owner_id,
                    project_id=storyboard.project_id
                )
                db.add(job)
                db.commit()
                db.refresh(job)
                shot.render_job_id = job.id
                db.commit()

            # Execute run generation inline
            def shot_progress_callback(percent: int):
                shot_contrib = 75 / total_shots
                overall = 5 + int((idx * shot_contrib) + (percent / 100 * shot_contrib))
                storyboard.progress = min(80, overall)
                db.commit()
                broadcast_storyboard_progress(storyboard.progress, "RUNNING")
                
            # Perform inference
            result = pipeline_orchestrator.run_generation(
                job_id=job.id,
                job_type=job.job_type,
                prompt=job.prompt,
                negative_prompt=job.negative_prompt,
                aspect_ratio=job.aspect_ratio,
                duration=job.duration,
                steps=job.steps,
                cfg_scale=job.cfg_scale,
                seed=job.seed,
                motion_strength=job.motion_strength,
                fps=job.fps,
                model_version=job.model_version,
                progress_callback=shot_progress_callback
            )
            
            # Save results to shot render job
            job.status = "SUCCESS"
            job.progress = 100
            job.result_url = result["video_url"]
            job.thumbnail_url = result["thumbnail_url"]
            job.gif_url = result["gif_url"]
            job.metadata_url = result["metadata_url"]
            job.seed = result["metadata"]["seed"]
            db.commit()

        storyboard.progress = 85
        db.commit()
        broadcast_storyboard_progress(85, "RUNNING")

        # 3. Stitch generated videos with timeline transitions
        local_video_paths = []
        transitions = []
        
        # Check timeline items
        timeline = db.query(models.Timeline).filter(models.Timeline.storyboard_id == storyboard_id).first()
        timeline_items_map = {}
        if timeline:
            layers = db.query(models.Layer).filter(models.Layer.timeline_id == timeline.id).all()
            for layer in layers:
                items = db.query(models.TimelineItem).filter(models.TimelineItem.layer_id == layer.id).order_by(models.TimelineItem.start_time.asc()).all()
                for item in items:
                    if item.shot_id:
                        timeline_items_map[item.shot_id] = item

        for shot in shots_ordered:
            job = db.query(models.RenderJob).filter(models.RenderJob.id == shot.render_job_id).first()
            if job and job.result_url:
                if job.result_url.startswith("http"):
                    res = httpx.get(job.result_url)
                    res.raise_for_status()
                    fd, temp_path = tempfile.mkstemp(suffix=".mp4")
                    with open(temp_path, "wb") as f:
                        f.write(res.content)
                    os.close(fd)
                    local_video_paths.append(temp_path)
                else:
                    rel_path = job.result_url.lstrip("/")
                    full_path = os.path.join("/Users/darshanchopda/Desktop/image to vieo/backend", rel_path)
                    local_video_paths.append(full_path)
                
                t_item = timeline_items_map.get(shot.id)
                transitions.append(t_item.transition_out if t_item else None)

        # Compile stitched video
        storyboard.progress = 90
        db.commit()
        broadcast_storyboard_progress(90, "RUNNING")
        
        stitched_bytes = StoryboardManager.compile_storyboard_video(local_video_paths, transitions, fps=8)
        
        # Clean up downloaded remote files
        for path in local_video_paths:
            if "tmp" in path and os.path.exists(path):
                os.remove(path)

        # 4. Upload compiled storyboard MP4
        storyboard_metadata = {
            "storyboard_id": storyboard.id,
            "name": storyboard.name,
            "shot_count": total_shots,
            "description": storyboard.description
        }
        
        video_url, thumb_url, gif_url, meta_url = StorageManager.upload_generation_bundle(
            job_id=f"storyboard_{storyboard.id}",
            video_bytes=stitched_bytes,
            frames=[],
            params=storyboard_metadata
        )

        # 5. Save storyboard outcome
        storyboard.status = "SUCCESS"
        storyboard.progress = 100
        storyboard.result_url = video_url
        db.commit()
        
        broadcast_storyboard_progress(100, "SUCCESS", result_url=video_url)
        logger.info(f"Storyboard {storyboard_id} successfully compiled and uploaded.")
        return True

    except Exception as e:
        logger.exception(f"Error rendering storyboard {storyboard_id}: {e}")
        db.rollback()
        storyboard = db.query(models.Storyboard).filter(models.Storyboard.id == storyboard_id).first()
        if storyboard:
            storyboard.status = "FAILED"
            storyboard.error_message = str(e)
            db.commit()
            broadcast_storyboard_progress(storyboard.progress, "FAILED", error_message=str(e))
        return False
    finally:
        db.close()

def broadcast_audio_progress(
    user_id: int,
    audio_job_id: int,
    progress: int,
    status: str,
    result_url: str = None,
    error_message: str = None
):
    payload = {
        "user_id": user_id,
        "audio_job_id": audio_job_id,
        "progress": progress,
        "status": status,
        "result_url": result_url,
        "error_message": error_message
    }
    try:
        redis_client.publish("render_progress", json.dumps(payload))
    except Exception as e:
        logger.warning(f"Failed publishing audio progress to Redis: {e}")
        
    try:
        from .services.ws_manager import ws_manager
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(ws_manager.send_to_client(str(user_id), payload))
        except RuntimeError:
            asyncio.run(ws_manager.send_to_client(str(user_id), payload))
    except Exception as ws_err:
        logger.warning(f"Direct Audio WebSocket broadcast fallback failed: {ws_err}")

@shared_task(name="app.tasks.process_audio_task")
def process_audio_task(job_id: int):
    """
    Executes advanced Audio pipelines (TTS, STT, MusicGen, Speaker voice cloning).
    """
    from .ai.audio_pipeline import AudioPipeline
    
    logger.info(f"Task: Starting process audio job {job_id}...")
    db = SessionLocal()
    
    job = db.query(models.AudioJob).filter(models.AudioJob.id == job_id).first()
    if not job:
        logger.error(f"AudioJob {job_id} not found in database.")
        db.close()
        return False
        
    try:
        job.status = "RUNNING"
        job.progress = 10
        db.commit()
        
        broadcast_audio_progress(job.user_id, job.id, 10, "RUNNING")
        
        renders_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "renders")
        os.makedirs(renders_dir, exist_ok=True)
        
        if job.job_type == "tts":
            filename = f"tts_{job.id}.wav"
            out_path = os.path.join(renders_dir, filename)
            
            emb_path = None
            if job.voice_profile_id:
                vp = db.query(models.VoiceProfile).filter(models.VoiceProfile.id == job.voice_profile_id).first()
                if vp:
                    emb_path = vp.embedding_path
                    
            AudioPipeline.text_to_speech(job.prompt or "Hello from Aetheria", emb_path, out_path)
            
            job.result_url = f"/static/renders/{filename}"
            job.progress = 100
            job.status = "SUCCESS"
            db.commit()
            
            broadcast_audio_progress(job.user_id, job.id, 100, "SUCCESS", result_url=job.result_url)
            
        elif job.job_type == "stt":
            filename = f"stt_{job.id}.wav"
            dummy_path = os.path.join(renders_dir, filename)
            if not os.path.exists(dummy_path):
                with open(dummy_path, "wb") as f:
                    f.write(b"RIFF\x24\x08\x00\x00WAVE")
            
            segments = AudioPipeline.speech_to_text(dummy_path)
            
            for seg in segments:
                sub = models.Subtitle(
                    text=seg["text"],
                    start_time=seg["start"],
                    end_time=seg["end"],
                    render_job_id=job.id
                )
                db.add(sub)
            db.commit()
            
            job.result_url = f"/static/renders/{filename}"
            job.progress = 100
            job.status = "SUCCESS"
            db.commit()
            
            broadcast_audio_progress(job.user_id, job.id, 100, "SUCCESS", result_url=job.result_url)
            
        elif job.job_type == "music":
            filename = f"music_{job.id}.wav"
            out_path = os.path.join(renders_dir, filename)
            
            AudioPipeline.generate_background_music(job.prompt or "Lo-fi synth background", 10, out_path)
            
            job.result_url = f"/static/renders/{filename}"
            job.progress = 100
            job.status = "SUCCESS"
            db.commit()
            
            broadcast_audio_progress(job.user_id, job.id, 100, "SUCCESS", result_url=job.result_url)
            
        elif job.job_type == "cloning":
            filename = f"clone_{job.id}.npy"
            out_path = os.path.join(renders_dir, filename)
            
            dummy_wav = os.path.join(renders_dir, f"voice_{job.id}.wav")
            with open(dummy_wav, "wb") as f:
                f.write(b"RIFF\x24\x08\x00\x00WAVE")
                
            AudioPipeline.voice_cloning_extract(dummy_wav, out_path)
            
            if job.voice_profile_id:
                vp = db.query(models.VoiceProfile).filter(models.VoiceProfile.id == job.voice_profile_id).first()
                if vp:
                    vp.embedding_path = f"/static/renders/{filename}"
                    db.add(vp)
            
            job.result_url = f"/static/renders/{filename}"
            job.progress = 100
            job.status = "SUCCESS"
            db.commit()
            
            broadcast_audio_progress(job.user_id, job.id, 100, "SUCCESS", result_url=job.result_url)
            
        else:
            raise ValueError(f"Unknown audio job type: {job.job_type}")
            
        logger.info(f"AudioJob {job_id} executed successfully.")
        return True
        
    except Exception as e:
        logger.exception(f"Error processing audio job {job_id}: {e}")
        db.rollback()
        job = db.query(models.AudioJob).filter(models.AudioJob.id == job_id).first()
        if job:
            job.status = "FAILED"
            job.error_message = str(e)
            db.commit()
            broadcast_audio_progress(job.user_id, job.id, job.progress, "FAILED", error_message=str(e))
        return False
    finally:
        db.close()

def broadcast_training_progress(
    user_id: int,
    ft_job_id: int,
    progress: int,
    status: str,
    metrics: str = None,
    error_message: str = None
):
    payload = {
        "user_id": user_id,
        "fine_tuning_job_id": ft_job_id,
        "progress": progress,
        "status": status,
        "metrics": metrics,
        "error_message": error_message
    }
    try:
        redis_client.publish("render_progress", json.dumps(payload))
    except Exception as e:
        logger.warning(f"Failed publishing fine-tuning progress to Redis: {e}")
        
    try:
        from .services.ws_manager import ws_manager
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(ws_manager.send_to_client(str(user_id), payload))
        except RuntimeError:
            asyncio.run(ws_manager.send_to_client(str(user_id), payload))
    except Exception as ws_err:
        logger.warning(f"Direct MLOps WebSocket broadcast fallback failed: {ws_err}")

@shared_task(name="app.tasks.run_fine_tuning_task")
def run_fine_tuning_task(job_id: int):
    """
    Simulates ML MLOps pipelines DreamBooth/LoRA model training loops.
    """
    from .services.mlops_manager import MLOpsManager
    
    logger.info(f"Task: Starting fine-tuning training job {job_id}...")
    db = SessionLocal()
    
    job = db.query(models.FineTuningJob).filter(models.FineTuningJob.id == job_id).first()
    if not job:
        logger.error(f"FineTuningJob {job_id} not found in database.")
        db.close()
        return False
        
    try:
        job.status = "RUNNING"
        job.progress = 5
        db.commit()
        
        broadcast_training_progress(job.owner_id, job.id, 5, "RUNNING")
        
        dataset = db.query(models.Dataset).filter(models.Dataset.id == job.dataset_id).first()
        if dataset:
            report = MLOpsManager.validate_and_caption_dataset(dataset.storage_path)
            dataset.status = "VALIDATED"
            dataset.auto_captions = json.dumps(report["auto_captions"])
            db.commit()
            
        metrics_history = []
        for epoch in range(1, job.epochs + 1):
            time.sleep(0.1) # simulation delay
            step_log = MLOpsManager.execute_training_step(epoch, job.epochs, job.learning_rate)
            metrics_history.append(step_log)
            
            progress_pct = int(10 + (float(epoch) / float(job.epochs)) * 85)
            job.progress = progress_pct
            job.metrics = json.dumps(metrics_history)
            db.commit()
            
            broadcast_training_progress(job.owner_id, job.id, progress_pct, "RUNNING", metrics=job.metrics)
            
        job.status = "SUCCESS"
        job.progress = 100
        job.result_model_path = f"/static/models/{job.model_name}_v1.safetensors"
        
        model_version = models.ModelVersion(
            name=job.model_name,
            version="1.0.0",
            path=job.result_model_path,
            active=True
        )
        db.add(model_version)
        db.commit()
        
        broadcast_training_progress(job.owner_id, job.id, 100, "SUCCESS", metrics=job.metrics)
        logger.info(f"FineTuningJob {job_id} completed successfully and model registered.")
        return True
        
    except Exception as e:
        logger.exception(f"Error training fine-tuning job {job_id}: {e}")
        db.rollback()
        job = db.query(models.FineTuningJob).filter(models.FineTuningJob.id == job_id).first()
        if job:
            job.status = "FAILED"
            job.error_message = str(e)
            db.commit()
            broadcast_training_progress(job.owner_id, job.id, job.progress, "FAILED", error_message=str(e))
        return False
    finally:
        db.close()
