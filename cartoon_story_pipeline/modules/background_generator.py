# modules/background_generator.py
import os

def generate_backgrounds(scene_prompts, config):
    os.makedirs("assets/backgrounds", exist_ok=True)
    background_paths = []

    for idx, prompt in enumerate(scene_prompts):
        bg_path = f"assets/backgrounds/bg_{idx+1}.png"
        # TEMP placeholder: just create an empty file
        with open(bg_path, "w") as f:
            f.write(f"BACKGROUND_PLACEHOLDER: {prompt}")
        background_paths.append(bg_path)

    return background_paths
