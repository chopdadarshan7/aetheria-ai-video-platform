import pytest
from app import models
from app.services.storyboard_manager import StoryboardManager
from app.tasks import render_storyboard_task
from PIL import Image

def test_storyboard_creation_db(db):
    # Verify Storyboard entity commits to DB
    storyboard = models.Storyboard(
        name="Sci-Fi Intro Trailer",
        description="Epic neon spaceship tracking shots",
        owner_id=1,
        status="PENDING",
        progress=0
    )
    db.add(storyboard)
    db.commit()
    db.refresh(storyboard)
    
    assert storyboard.id is not None
    assert storyboard.name == "Sci-Fi Intro Trailer"
    assert storyboard.status == "PENDING"

def test_storyboard_scenes_and_shots(db):
    # Verify Scene and Shot cascades
    storyboard = models.Storyboard(name="Epic Storyboard", owner_id=1)
    db.add(storyboard)
    db.commit()

    scene = models.Scene(name="Scene 1", order=0, storyboard_id=storyboard.id)
    db.add(scene)
    db.commit()
    db.refresh(scene)

    shot = models.Shot(
        name="Wide establishing shot",
        order=0,
        scene_id=scene.id,
        prompt="Spacestation hovering near blue gas giant, 8k",
        model_version="cogvideox-2b"
    )
    db.add(shot)
    db.commit()
    db.refresh(shot)

    assert shot.id is not None
    assert shot.scene_id == scene.id
    assert scene.storyboard_id == storyboard.id
    assert len(scene.shots) == 1

def test_timeline_and_transition_items(db):
    # Verify Timeline, Layers and items creation
    storyboard = models.Storyboard(name="Storyboard Timeline", owner_id=1)
    db.add(storyboard)
    db.commit()

    timeline = models.Timeline(storyboard_id=storyboard.id)
    db.add(timeline)
    db.commit()

    layer = models.Layer(timeline_id=timeline.id, name="Video Track", layer_type="video")
    db.add(layer)
    db.commit()

    item = models.TimelineItem(
        layer_id=layer.id,
        start_time=0.0,
        duration=5.0,
        transition_out="cross-dissolve"
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    assert item.id is not None
    assert item.layer_id == layer.id
    assert item.transition_out == "cross-dissolve"

def test_storyboard_compilation_stitching(tmp_path):
    # Verify StoryboardManager compiles multiple shots with transition blends
    # Create mock MP4 video files locally
    import tempfile
    import os
    import cv2
    import numpy as np

    # Build 2 tiny mock video files using opencv
    video1_path = os.path.join(tmp_path, "shot1.mp4")
    video2_path = os.path.join(tmp_path, "shot2.mp4")

    for path, color in [(video1_path, (255, 0, 0)), (video2_path, (0, 0, 255))]:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(path, fourcc, 8, (64, 36))
        for _ in range(8):
            frame = np.zeros((36, 64, 3), dtype=np.uint8)
            frame[:] = color
            out.write(frame)
        out.release()

    # Stitch them using cross-dissolve transition
    stitched_bytes = StoryboardManager.compile_storyboard_video(
        video_paths=[video1_path, video2_path],
        transitions=["cross-dissolve", None],
        fps=8
    )

    assert len(stitched_bytes) > 100 # stitched MP4 binary data generated
    assert b"ftyp" in stitched_bytes or b"moov" in stitched_bytes
