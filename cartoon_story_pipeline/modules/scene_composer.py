# modules/scene_compositor.py
import os
from PIL import Image

def compose_scenes(scene_prompts, background_paths, config):
    os.makedirs("exports/scenes", exist_ok=True)
    scene_paths = []

    for idx, bg_path in enumerate(background_paths):
        # Load BG
        bg_img = Image.new("RGBA", (1024, 768), (200, 200, 200, 255)) # Placeholder

        # Load character PNG (placeholder Milo)
        char_img = Image.new("RGBA", (200, 400), (255, 0, 0, 255)) # Red placeholder block

        # Composite
        bg_img.paste(char_img, (400, 300), char_img)
        scene_path = f"exports/scenes/scene_{idx+1}.png"
        bg_img.save(scene_path)
        scene_paths.append(scene_path)

    return scene_paths
