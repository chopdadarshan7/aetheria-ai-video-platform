import logging
import os
import tempfile
import cv2
import numpy as np
from typing import List, Tuple

logger = logging.getLogger(__name__)

class StoryboardManager:
    @staticmethod
    def blend_frames_cross_dissolve(frames1: List[np.ndarray], frames2: List[np.ndarray], blend_len: int) -> List[np.ndarray]:
        """Apply a cross-dissolve alpha blend transition between two frame lists."""
        blended = []
        for i in range(blend_len):
            alpha = (i + 1) / (blend_len + 1)
            # Blend frame1 and frame2: frame = (1 - alpha)*f1 + alpha*f2
            f1 = frames1[-blend_len + i]
            f2 = frames2[i]
            # Ensure dimensions match
            if f1.shape != f2.shape:
                f2_resized = cv2.resize(f2, (f1.shape[1], f1.shape[0]))
                blended_frame = cv2.addWeighted(f1, 1.0 - alpha, f2_resized, alpha, 0)
            else:
                blended_frame = cv2.addWeighted(f1, 1.0 - alpha, f2, alpha, 0)
            blended.append(blended_frame)
        return blended

    @staticmethod
    def apply_fade_transition(frames: List[np.ndarray], fade_len: int, fade_in: bool = True) -> List[np.ndarray]:
        """Apply fade-in (from black) or fade-out (to black) transition overlays."""
        faded = []
        for i in range(fade_len):
            alpha = (i + 1) / (fade_len + 1)
            scale = alpha if fade_in else (1.0 - alpha)
            frame = frames[i] if fade_in else frames[-fade_len + i]
            black = np.zeros_like(frame)
            blended_frame = cv2.addWeighted(black, 1.0 - scale, frame, scale, 0)
            faded.append(blended_frame)
        return faded

    @classmethod
    def compile_storyboard_video(cls, video_paths: List[str], transitions: List[str], fps: int = 8) -> bytes:
        """
        Reads frame sequences from multiple MP4 files, applies transitions
        (fade, cross-dissolve), and compiles them into a single stitched MP4 file.
        """
        if not video_paths:
            return b""

        logger.info(f"Storyboard compile starting for {len(video_paths)} video inputs...")
        
        all_frames: List[np.ndarray] = []
        shot_frames_list: List[List[np.ndarray]] = []
        width, height = 512, 288 # fallback dimensions

        # 1. Read frames from all input videos
        for path in video_paths:
            frames = []
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                logger.warning(f"Could not open video clip {path}. Skipping in compile.")
                continue
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
                
            cap.release()
            if frames:
                shot_frames_list.append(frames)
                height, width, _ = frames[0].shape

        if not shot_frames_list:
            logger.error("No valid video frames loaded for storyboard compile.")
            return b"NO_FRAMES_COMPILED"

        # 2. Sequence shots and stitch transitions
        # We process transitions between Shot[i] and Shot[i+1]
        transition_len = min(4, min(len(s) for s in shot_frames_list) // 3) # duration of transition
        
        current_shot_idx = 0
        while current_shot_idx < len(shot_frames_list):
            frames = shot_frames_list[current_shot_idx]
            transition = transitions[current_shot_idx] if current_shot_idx < len(transitions) else None
            
            # If this is not the last shot and a cross-dissolve transition is requested
            if transition == "cross-dissolve" and current_shot_idx < len(shot_frames_list) - 1:
                next_frames = shot_frames_list[current_shot_idx + 1]
                
                # Append base frames of current shot minus the overlap
                all_frames.extend(frames[:-transition_len])
                
                # Append blend frames
                blend = cls.blend_frames_cross_dissolve(frames, next_frames, transition_len)
                all_frames.extend(blend)
                
                # Crop transition frames off the beginning of next shot
                shot_frames_list[current_shot_idx + 1] = next_frames[transition_len:]
                
            elif transition == "fade" and len(frames) > transition_len * 2:
                # Fade out current shot
                fade_out_frames = cls.apply_fade_transition(frames, transition_len, fade_in=False)
                all_frames.extend(frames[:-transition_len])
                all_frames.extend(fade_out_frames)
                
                # If next shot exists, fade it in
                if current_shot_idx < len(shot_frames_list) - 1:
                    next_frames = shot_frames_list[current_shot_idx + 1]
                    fade_in_frames = cls.apply_fade_transition(next_frames, transition_len, fade_in=True)
                    all_frames.extend(fade_in_frames)
                    shot_frames_list[current_shot_idx + 1] = next_frames[transition_len:]
            else:
                # Direct cuts / static stitch
                all_frames.extend(frames)
                
            current_shot_idx += 1

        # 3. Write all stitched frames to output MP4 binary stream
        fd, temp_path = tempfile.mkstemp(suffix=".mp4")
        try:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
            for frame in all_frames:
                out.write(frame)
            out.release()
            
            with open(temp_path, "rb") as f:
                output_bytes = f.read()
        finally:
            os.close(fd)
            if os.path.exists(temp_path):
                os.remove(temp_path)

        logger.info(f"Storyboard compile finished. Stitched frame count: {len(all_frames)}.")
        return output_bytes
