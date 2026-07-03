import pytest
import os
import numpy as np
from app import models
from app.ai.audio_pipeline import AudioPipeline

def test_voice_profile_db(db):
    # Verify voice profile mapping and commits
    vp = models.VoiceProfile(
        name="Morgan Freeman Presets",
        language="en",
        owner_id=1
    )
    db.add(vp)
    db.commit()
    db.refresh(vp)
    
    assert vp.id is not None
    assert vp.name == "Morgan Freeman Presets"
    assert vp.language == "en"

def test_subtitle_segmentation(db):
    # Verify storyboard subtitlestimed loops
    subtitle = models.Subtitle(
        text="Narrator: Deep in the solar system...",
        start_time=0.0,
        end_time=3.5,
        storyboard_id=1
    )
    db.add(subtitle)
    db.commit()
    db.refresh(subtitle)

    assert subtitle.id is not None
    assert subtitle.text == "Narrator: Deep in the solar system..."
    assert subtitle.end_time == 3.5

def test_audio_pipeline_tts(tmp_path):
    # Verify AudioPipeline generates TTS audio file
    out_path = os.path.join(tmp_path, "narration.wav")
    AudioPipeline.text_to_speech(
        text="Establishing wide tracking shot on orbit.",
        voice_profile_emb_path=None,
        output_path=out_path
    )
    
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 44

def test_audio_pipeline_stt():
    # Verify transcription segments are returned
    segments = AudioPipeline.speech_to_text("dummy.wav")
    assert len(segments) == 2
    assert segments[0]["text"] == "Welcome to Aetheria AI Creative Studio."

def test_audio_pipeline_voice_clone(tmp_path):
    # Verify mock voice profile NumPy embeddings save correctly
    emb_path = os.path.join(tmp_path, "embeddings.npy")
    AudioPipeline.voice_cloning_extract("dummy.wav", emb_path)
    
    assert os.path.exists(emb_path)
    embeddings = np.load(emb_path)
    assert embeddings.shape == (128,)
