import io
import json
import logging
from typing import List, Dict, Any, Tuple
from PIL import Image
import boto3
from ..config import settings

logger = logging.getLogger(__name__)

class StorageManager:
    @staticmethod
    def get_s3_client():
        return boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
        )

    @staticmethod
    def generate_thumbnail(first_frame: Image.Image) -> bytes:
        """Create a JPEG thumbnail from the first image frame."""
        thumb = first_frame.copy()
        thumb.thumbnail((320, 180)) # standard 16:9 thumbnail size
        buf = io.BytesIO()
        thumb.save(buf, format="JPEG", quality=85)
        return buf.getvalue()

    @staticmethod
    def generate_preview_gif(frames: List[Image.Image]) -> bytes:
        """Compile a low-res preview GIF from generated video frames."""
        if not frames:
            return b""
        
        # Keep maximum of 10 frames to optimize size
        stride = max(1, len(frames) // 10)
        gif_frames = [f.copy() for f in frames[::stride]]
        
        # Resize to smaller dimensions
        for f in gif_frames:
            f.thumbnail((256, 144))
            
        buf = io.BytesIO()
        gif_frames[0].save(
            buf,
            format="GIF",
            save_all=True,
            append_images=gif_frames[1:],
            duration=150, # millisecond delay between frames
            loop=0
        )
        return buf.getvalue()

    @staticmethod
    def upload_generation_bundle(
        job_id: int,
        video_bytes: bytes,
        frames: List[Image.Image],
        params: Dict[str, Any]
    ) -> Tuple[str, str, str, str]:
        """
        Build and upload the complete output bundle (video, thumbnail, gif, metadata)
        to storage, returning their URLs.
        """
        s3 = StorageManager.get_s3_client()
        bucket = settings.S3_BUCKET_NAME

        try:
            # Ensure S3 Bucket exists
            try:
                s3.head_bucket(Bucket=bucket)
            except Exception:
                try:
                    s3.create_bucket(Bucket=bucket)
                except Exception as e:
                    logger.warning(f"Could not create bucket '{bucket}': {e}")

            # 1. Video file
            s3.put_object(Bucket=bucket, Key=video_key, Body=video_bytes, ContentType="video/mp4")
            video_url = f"{settings.S3_ENDPOINT_URL}/{bucket}/{video_key}"

            # 2. Thumbnail
            thumb_url = ""
            if frames:
                try:
                    thumb_bytes = StorageManager.generate_thumbnail(frames[0])
                    s3.put_object(Bucket=bucket, Key=thumb_key, Body=thumb_bytes, ContentType="image/jpeg")
                    thumb_url = f"{settings.S3_ENDPOINT_URL}/{bucket}/{thumb_key}"
                except Exception as e:
                    logger.error(f"Error generating thumbnail for job {job_id}: {e}")

            # 3. GIF Preview
            gif_url = ""
            if len(frames) > 1:
                try:
                    gif_bytes = StorageManager.generate_preview_gif(frames)
                    s3.put_object(Bucket=bucket, Key=gif_key, Body=gif_bytes, ContentType="image/gif")
                    gif_url = f"{settings.S3_ENDPOINT_URL}/{bucket}/{gif_key}"
                except Exception as e:
                    logger.error(f"Error generating preview GIF for job {job_id}: {e}")

            # 4. Metadata JSON
            meta_url = ""
            try:
                meta_content = json.dumps(params, indent=2).encode("utf-8")
                s3.put_object(Bucket=bucket, Key=meta_key, Body=meta_content, ContentType="application/json")
                meta_url = f"{settings.S3_ENDPOINT_URL}/{bucket}/{meta_key}"
            except Exception as e:
                logger.error(f"Error generating metadata JSON for job {job_id}: {e}")

            return video_url, thumb_url, gif_url, meta_url

        except Exception as upload_err:
            logger.warning(f"Failed uploading job {job_id} bundle to S3 ({upload_err}). Falling back to local filesystem storage.")
            import os
            # Save files locally
            local_dir = f"/Users/darshanchopda/Desktop/image to vieo/backend/static/renders/job_{job_id}"
            os.makedirs(local_dir, exist_ok=True)
            
            # Save video
            video_path = os.path.join(local_dir, "video.mp4")
            with open(video_path, "wb") as f:
                f.write(video_bytes)
            video_url = f"/static/renders/job_{job_id}/video.mp4"

            # Save thumbnail
            thumb_url = ""
            if frames:
                try:
                    thumb_bytes = StorageManager.generate_thumbnail(frames[0])
                    thumb_path = os.path.join(local_dir, "thumb.jpg")
                    with open(thumb_path, "wb") as f:
                        f.write(thumb_bytes)
                    thumb_url = f"/static/renders/job_{job_id}/thumb.jpg"
                except Exception as th_err:
                    logger.error(f"Error generating local thumbnail for job {job_id}: {th_err}")

            # Save GIF Preview
            gif_url = ""
            if len(frames) > 1:
                try:
                    gif_bytes = StorageManager.generate_preview_gif(frames)
                    gif_path = os.path.join(local_dir, "preview.gif")
                    with open(gif_path, "wb") as f:
                        f.write(gif_bytes)
                    gif_url = f"/static/renders/job_{job_id}/preview.gif"
                except Exception as gif_err:
                    logger.error(f"Error generating local GIF preview for job {job_id}: {gif_err}")

            # Save Metadata JSON
            meta_url = ""
            try:
                meta_content = json.dumps(params, indent=2).encode("utf-8")
                meta_path = os.path.join(local_dir, "metadata.json")
                with open(meta_path, "wb") as f:
                    f.write(meta_content)
                meta_url = f"/static/renders/job_{job_id}/metadata.json"
            except Exception as meta_err:
                logger.error(f"Error generating local metadata for job {job_id}: {meta_err}")

            return video_url, thumb_url, gif_url, meta_url
