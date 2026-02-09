import os
import json
from PIL import Image

def compose_scenes(scene_prompts, config):
    os.makedirs("exports/scenes", exist_ok=True)
    artifacts_folder = "assets/background_artifacts"
    layout_file = os.path.join(artifacts_folder, "layout.json")

    # Load predefined layouts
    layouts = {}
    if os.path.exists(layout_file):
        with open(layout_file, "r") as f:
            layouts = json.load(f)

    scene_paths = []

    for idx, _ in enumerate(scene_prompts):
        # Create minimalist base (white background)
        bg_img = Image.new("RGBA", config.get("background_image_size", [1024, 768]), (255, 255, 255, 255))

        # Select layout
        layout_key = list(layouts.keys())[idx % len(layouts)]
        for art in layouts[layout_key]:
            art_path = os.path.join(artifacts_folder, art["file"])
            if os.path.exists(art_path):
                art_img = Image.open(art_path).convert("RGBA")
                bg_img.paste(art_img, tuple(art["position"]), art_img)

        # Add fixed character rig
        char_folder = os.path.join("assets/characters", config["character_default"])
        char_path = os.path.join(char_folder, "idle.png")
        if os.path.exists(char_path):
            char_img = Image.open(char_path).convert("RGBA")
            bg_img.paste(char_img, (400, 300), char_img)

        scene_path = f"exports/scenes/scene_{idx+1}.png"
        bg_img.save(scene_path)
        scene_paths.append(scene_path)

    return scene_paths
