import pytest
from app.ai.prompt_engine import PromptEngine
from app.ai.model_manager import ModelManager, MockPipeline
from app.ai.pipeline import AIPipeline
from PIL import Image

def test_prompt_engine_parser():
    # Verify keyword and tags parsing
    raw_prompt = "A girl running on a sunny beach during sunset with zoom camera movement"
    parsed = PromptEngine.parse_prompt(raw_prompt)
    
    assert parsed["subject"] == "girl"
    assert parsed["action"] == "running"
    assert parsed["location"] == "sunny beach"
    assert parsed["camera"] == "zoom"
    assert parsed["style"] == "cinematic" # default fallback
    assert parsed["lighting"] == "sunset"
    assert parsed["weather"] == "sunny"
    assert parsed["aspect_ratio"] == "16:9"

def test_prompt_engine_enhancer():
    # Verify visual tags appending and negative presets mapping
    raw_prompt = "A cute cat standing vaporwave 1:1"
    enhanced, negative = PromptEngine.enhance_prompt(raw_prompt)
    
    assert "vaporwave" in enhanced
    assert "cat" in enhanced
    assert "1:1" not in enhanced # aspect ratio tags are consumed in metadata params
    assert len(negative) > 10

def test_model_manager_registry():
    # Verify listed registered models
    manager = ModelManager()
    models_list = manager.list_models()
    
    assert "svd-xt" in models_list
    assert "cogvideox-2b" in models_list
    assert models_list["svd-xt"]["repo_id"] == "stabilityai/stable-video-diffusion-img2vid-xt"
    assert models_list["svd-xt"]["type"] == "image-to-video"

def test_mock_pipeline_call():
    # Verify mock pipeline yields frame list sequence fallback
    pipeline = MockPipeline("mock-repo")
    output = pipeline()
    
    assert hasattr(output, "frames")
    assert len(output.frames) == 8
    assert isinstance(output.frames[0], Image.Image)

def test_ai_pipeline_mock_run():
    # Verify complete pipeline generation loop using Mock pipeline
    manager = ModelManager()
    orchestrator = AIPipeline(manager)
    
    # We trace progress ticks
    ticks = []
    def callback(percent):
        ticks.append(percent)

    result = orchestrator.run_generation(
        job_id=999,
        job_type="text-to-video",
        prompt="A bird flying high speed",
        aspect_ratio="16:9",
        duration=5,
        steps=25,
        cfg_scale=7.0,
        seed=12345,
        progress_callback=callback
    )

    assert "video_url" in result
    assert "thumbnail_url" in result
    assert "gif_url" in result
    assert "metadata" in result
    
    # Check that progress ticks reached 100
    assert 100 in ticks
    assert result["metadata"]["seed"] == 12345
    assert result["metadata"]["model_version"] == "cogvideox-2b"
