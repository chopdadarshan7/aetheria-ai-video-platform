import re
from typing import Dict, Any, Tuple

# Pre-defined keyword matching patterns
CAMERA_MOVEMENTS = [
    "tracking shot", "pan shot", "zoom", "static", "dolly shot", "crane shot", 
    "bird's-eye view", "drone shot", "close up", "extreme close-up", "wide shot"
]

STYLES = [
    "cinematic", "photorealistic", "3d render", "anime", "claymation", "retro", 
    "cyberpunk", "vaporwave", "oil painting", "watercolor", "sketch", "digital art"
]

LIGHTING = [
    "sunset", "neon glowing", "studio lighting", "dramatic backlight", 
    "volumetric rays", "golden hour", "natural light", "harsh shadows", "ambient glow"
]

WEATHER = [
    "clear sky", "rainy", "foggy", "snowy", "stormy", "cloudy", "sunny"
]

MOTIONS = [
    "slow motion", "fast-paced", "high speed", "jittery", "smooth fluid motion", "static"
]

ASPECT_RATIOS = {
    "16:9": ["16:9", "widescreen", "cinema", "landscape"],
    "9:16": ["9:16", "portrait", "vertical", "tiktok", "reel"],
    "1:1": ["1:1", "square", "instagram"]
}

class PromptEngine:
    @staticmethod
    def parse_prompt(prompt: str) -> Dict[str, Any]:
        """Convert raw text prompt into structured tags using regex keyword matching."""
        prompt_lower = prompt.lower()
        
        # 1. Subject & Action (Simple fallback parser using token structures)
        # Match "A [subject] [action] on/in [location]"
        subject = "character"
        action = "existing"
        location = "abstract environment"
        
        # A simple regex to grab common descriptive noun phrase patterns
        match = re.search(r"(?:a|an)\s+([a-zA-Z\s\-]+?)\s+(?:running|walking|flying|standing|sitting|dancing|talking|singing|looking|riding|driving|jumping)\s+", prompt, re.IGNORECASE)
        if match:
            subject = match.group(1).strip()
            
        action_match = re.search(r"\b(running|walking|flying|standing|sitting|dancing|talking|singing|looking|riding|driving|jumping)\b", prompt_lower)
        if action_match:
            action = action_match.group(1)
            
        loc_match = re.search(r"\b(?:on|in|at|near|over|under|inside)\s+(?:a|an|the)?\s*([a-zA-Z\s\-]+?)(?:\.|\b(?:during|with|under|in)\b|$)", prompt, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip()

        # 2. Match categorized keywords
        camera = next((c for c in CAMERA_MOVEMENTS if c in prompt_lower), "static")
        style = next((s for s in STYLES if s in prompt_lower), "cinematic")
        lighting = next((l for l in LIGHTING if l in prompt_lower), "natural light")
        weather = next((w for w in WEATHER if w in prompt_lower), "clear")
        motion = next((m for m in MOTIONS if m in prompt_lower), "normal")

        # 3. Detect Aspect Ratio
        detected_ar = "16:9" # default
        for ar, keywords in ASPECT_RATIOS.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected_ar = ar
                break

        return {
            "subject": subject,
            "action": action,
            "location": location,
            "camera": camera,
            "style": style,
            "weather": weather,
            "lighting": lighting,
            "motion": motion,
            "aspect_ratio": detected_ar
        }

    @staticmethod
    def enhance_prompt(prompt: str) -> Tuple[str, str]:
        """
        Enhance a user prompt into a high-fidelity creative text prompt
        and generate a custom negative prompt preset.
        """
        parsed = PromptEngine.parse_prompt(prompt)
        
        # Build enhanced visual prompts using visual modifiers
        enhanced_prompt = (
            f"A professional, ultra-detailed {parsed['style']} shot of a {parsed['subject']} "
            f"actively {parsed['action']} in a {parsed['location']}. "
            f"Atmosphere: {parsed['weather']} weather, captured during {parsed['lighting']}. "
            f"Camera characteristics: {parsed['camera']}, featuring {parsed['motion']}, "
            f"captured in 8k resolution, highly detailed textures, masterfully graded color."
        )
        
        # Build negative prompt matching the target style
        negative_prompt = (
            "blurry, low quality, noise, grain, text overlay, signature, watermark, "
            "deformed anatomy, disfigured limbs, bad lighting, extra fingers, cartoonish "
            "if photorealistic, static frames, jittery cuts, low resolution"
        )
        
        return enhanced_prompt, negative_prompt
