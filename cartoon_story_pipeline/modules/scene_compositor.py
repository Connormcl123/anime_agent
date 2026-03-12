import os
import json
from typing import Any, Dict, List, Tuple

from PIL import Image

from modules import background_generator


def _load_layouts(artifacts_folder: str) -> Dict[str, Any]:
    layout_file = os.path.join(artifacts_folder, "layout.json")
    if os.path.exists(layout_file):
        with open(layout_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _safe_filename(name: str) -> str:
    """
    Converts character names into a filename-friendly string.
    Example: "Good Samaritan" -> "Good_Samaritan"
    """
    name = name.strip()
    name = name.replace("/", "-").replace("\\", "-")
    name = "_".join(name.split())
    return name


def _character_image_path(character_name: str, config: Dict[str, Any]) -> str:
    """
    Your structure: assets/characters/<CharacterName>.png
    """
    characters_dir = config.get("characters_dir", "assets/characters")
    ext = config.get("character_file_ext", ".png")
    filename = _safe_filename(character_name) + ext
    return os.path.join(characters_dir, filename)


def _paste_character(bg_img: Image.Image, char_path: str, pos: Tuple[int, int]) -> None:
    if not os.path.exists(char_path):
        return

    char_img = Image.open(char_path).convert("RGBA")

    # Scale character to fit scene nicely
    max_w = int(bg_img.size[0] * 0.35)
    max_h = int(bg_img.size[1] * 0.55)
    if char_img.size[0] > max_w or char_img.size[1] > max_h:
        char_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

    bg_img.paste(char_img, pos, char_img)


def compose_scenes(story_data: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    """
    Composes scenes using:
    - OpenAI-generated backgrounds (optional) OR a minimalist white base
    - background_artifacts/layout.json overlays (optional)
    - character PNGs from assets/characters/<Name>.png (multiple per scene)
    """
    os.makedirs("exports/scenes", exist_ok=True)

    scenes = story_data.get("scenes", [])
    if not isinstance(scenes, list) or not scenes:
        # Backward compatibility: accept story_data["scene_prompts"]
        scene_prompts = story_data.get("scene_prompts", [])
        scenes = [{"id": i + 1, "prompt": p, "characters_in_scene": []} for i, p in enumerate(scene_prompts)]

    # Generate background images via OpenAI (optional)
    use_openai_bgs = bool(config.get("use_openai_backgrounds", False))
    background_paths: List[str] = []
    if use_openai_bgs:
        prompts = [s.get("prompt", "") for s in scenes]
        background_paths = background_generator.generate_backgrounds(prompts, config)

    artifacts_folder = "assets/background_artifacts"
    layouts = _load_layouts(artifacts_folder)

    scene_paths: List[str] = []
    size = tuple(config.get("background_image_size", [1024, 768]))

    # Simple “slots” for up to 3 characters
    slots = [
        (int(size[0] * 0.10), int(size[1] * 0.35)),  # left
        (int(size[0] * 0.40), int(size[1] * 0.35)),  # center
        (int(size[0] * 0.70), int(size[1] * 0.35)),  # right
    ]

    layout_keys = list(layouts.keys()) if layouts else []

    for idx, scene in enumerate(scenes):
        scene_id = scene.get("id", idx + 1)
        prompt = scene.get("prompt", "")
        chars = scene.get("characters_in_scene", []) or []

        print(f"[SCENE {scene_id}] prompt: {prompt[:70]}{'...' if len(prompt) > 70 else ''}")
        if chars:
            print(f"[SCENE {scene_id}] characters: {', '.join(chars)}")
        else:
            print(f"[SCENE {scene_id}] characters: (none listed)")

        # Base background
        if use_openai_bgs and idx < len(background_paths) and os.path.exists(background_paths[idx]):
            bg_img = Image.open(background_paths[idx]).convert("RGBA")
            if bg_img.size != size:
                bg_img = bg_img.resize(size, Image.Resampling.LANCZOS)
        else:
            bg_img = Image.new("RGBA", size, (255, 255, 255, 255))

        # Optional layout artifacts overlay
        if layout_keys:
            layout_key = layout_keys[idx % len(layout_keys)]
            for art in layouts.get(layout_key, []):
                art_path = os.path.join(artifacts_folder, art.get("file", ""))
                if os.path.exists(art_path):
                    art_img = Image.open(art_path).convert("RGBA")
                    pos = tuple(art.get("position", [0, 0]))
                    bg_img.paste(art_img, pos, art_img)

        # Paste characters (up to 3). If none listed, fall back to character_default.
        if not chars:
            chars = [config.get("character_default", "Jesus")]

        for c_i, character_name in enumerate(chars[:3]):
            char_path = _character_image_path(character_name, config)
            if not os.path.exists(char_path):
                print(f"[WARN] Missing character PNG: {char_path}")
            _paste_character(bg_img, char_path, slots[c_i])

        scene_path = f"exports/scenes/scene_{idx + 1}.png"
        bg_img.save(scene_path)
        scene_paths.append(scene_path)

    return scene_paths
