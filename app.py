"""
Wan2.1 Image-to-Video API — Actual Video Generation
====================================================
Deployed on Modal with A100-80GB GPU.
Downloads Wan2.1-I2V-14B-480P-Diffusers weights from Hugging Face at build time.

This API takes an input image and generates an animated MP4 video from it.

Official reference:
  https://huggingface.co/Wan-AI/Wan2.1-I2V-14B-480P-Diffusers
"""

import modal
import io

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_ID = "Wan-AI/Wan2.1-I2V-14B-480P-Diffusers"
MODEL_DIR = "/model-cache"

app = modal.App("wan21-image-to-video")

# ---------------------------------------------------------------------------
# Modal Volume to cache model weights (faster than baking ~60GB into image)
# ---------------------------------------------------------------------------
volume = modal.Volume.from_name("wan21-model-weights", create_if_missing=True)

# ---------------------------------------------------------------------------
# Image build: install all dependencies
# ---------------------------------------------------------------------------
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch",
        "torchvision",
        "diffusers",
        "transformers",
        "accelerate",
        "sentencepiece",
        "fastapi[standard]",
        "python-multipart",
        "pillow",
        "numpy",
    )
)


# ---------------------------------------------------------------------------
# Download model weights into the Volume (runs once)
# ---------------------------------------------------------------------------
@app.function(image=image, volumes={MODEL_DIR: volume}, timeout=3600)
def download_model():
    """Downloads Wan2.1-I2V-14B-480P-Diffusers weights from Hugging Face."""
    import torch
    from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
    from transformers import CLIPVisionModel

    print(f"⬇️  Downloading {MODEL_ID} from Hugging Face …")

    # Download each component separately so they are cached
    print("  → image_encoder …")
    CLIPVisionModel.from_pretrained(
        MODEL_ID, subfolder="image_encoder",
        torch_dtype=torch.float32, cache_dir=MODEL_DIR,
    )
    print("  → vae …")
    AutoencoderKLWan.from_pretrained(
        MODEL_ID, subfolder="vae",
        torch_dtype=torch.float32, cache_dir=MODEL_DIR,
    )
    print("  → full pipeline …")
    WanImageToVideoPipeline.from_pretrained(
        MODEL_ID, torch_dtype=torch.bfloat16, cache_dir=MODEL_DIR,
    )

    volume.commit()
    print("✅  All weights downloaded and saved to volume!")


# ---------------------------------------------------------------------------
# ASGI app — serves the image-to-video endpoint on an A100
# ---------------------------------------------------------------------------
@app.function(
    image=image,
    gpu="A100",
    volumes={MODEL_DIR: volume},
    timeout=600,
    scaledown_window=300,
)
@modal.asgi_app()
def web():
    """Creates a FastAPI app and loads Wan2.1 for actual video generation."""
    import torch
    import numpy as np
    from fastapi import FastAPI, UploadFile, File, Form
    from fastapi.responses import Response
    from fastapi.middleware.cors import CORSMiddleware
    from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
    from diffusers.utils import export_to_video, load_image
    from transformers import CLIPVisionModel
    from PIL import Image
    import tempfile
    import os

    # ------------------------------------------------------------------
    # Load the Wan2.1 pipeline
    # ------------------------------------------------------------------
    print(f"🚀  Loading {MODEL_ID} onto A100 GPU …")

    image_encoder = CLIPVisionModel.from_pretrained(
        MODEL_ID, subfolder="image_encoder",
        torch_dtype=torch.float32, cache_dir=MODEL_DIR,
    )
    vae = AutoencoderKLWan.from_pretrained(
        MODEL_ID, subfolder="vae",
        torch_dtype=torch.float32, cache_dir=MODEL_DIR,
    )
    pipe = WanImageToVideoPipeline.from_pretrained(
        MODEL_ID,
        vae=vae,
        image_encoder=image_encoder,
        torch_dtype=torch.bfloat16,
        cache_dir=MODEL_DIR,
    )
    pipe.to("cuda")

    print("✅  Wan2.1 pipeline loaded and ready!")

    # ------------------------------------------------------------------
    # FastAPI application
    # ------------------------------------------------------------------
    api = FastAPI(title="Wan2.1 Image-to-Video API")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @api.get("/health")
    async def health():
        return {"status": "ok", "model": MODEL_ID}

    @api.post("/generate-video")
    async def generate_video(
        file: UploadFile = File(...),
        prompt: str = Form(
            "A dynamic scene with subtle natural motion, high quality, "
            "cinematic lighting, smooth camera movement."
        ),
        num_frames: int = Form(81),
        guidance_scale: float = Form(5.0),
        num_inference_steps: int = Form(50),
    ):
        """Upload an image → get an animated MP4 video back."""
        # Read the uploaded image
        image_bytes = await file.read()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Calculate proper dimensions (from official docs)
        max_area = 480 * 832
        aspect_ratio = img.height / img.width
        mod_value = pipe.vae_scale_factor_spatial * pipe.transformer.config.patch_size[1]
        height = round(np.sqrt(max_area * aspect_ratio)) // mod_value * mod_value
        width = round(np.sqrt(max_area / aspect_ratio)) // mod_value * mod_value
        img = img.resize((width, height))

        negative_prompt = (
            "Bright tones, overexposed, static, blurred details, subtitles, "
            "style, works, paintings, images, static, overall gray, worst quality, "
            "low quality, JPEG compression residue, ugly, incomplete, extra fingers, "
            "poorly drawn hands, poorly drawn faces, deformed, disfigured, "
            "misshapen limbs, fused fingers, still picture, messy background"
        )

        print(f"🎬  Generating video: {width}x{height}, {num_frames} frames …")

        # Run inference
        output = pipe(
            image=img,
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=height,
            width=width,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
        ).frames[0]

        # Export to MP4
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            export_to_video(output, tmp.name, fps=16)
            tmp.seek(0)
            video_bytes = open(tmp.name, "rb").read()
            os.unlink(tmp.name)

        print(f"✅  Video generated! Size: {len(video_bytes) / 1024:.1f} KB")

        return Response(
            content=video_bytes,
            media_type="video/mp4",
            headers={
                "Content-Disposition": "attachment; filename=generated_video.mp4"
            },
        )

    return api
