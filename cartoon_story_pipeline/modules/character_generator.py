import base64
import os
from typing import Dict, Any, List

from openai import OpenAI


def _safe_filename(name: str) -> str:
    name = name.strip()
    name = name.replace("/", "-").replace("\\", "-")
    name = "_".join(name.split())
    return name


def _decode_image_to_file(image_b64: str, out_path: str) -> None:
    data = base64.b64decode(image_b64)
    with open(out_path, "wb") as f:
        f.write(data)


def _character_png_path(character_name: str, config: Dict[str, Any]) -> str:
    characters_dir = config.get("characters_dir", "assets/characters")
    ext = config.get("character_file_ext", ".png")
    os.makedirs(characters_dir, exist_ok=True)
    return os.path.join(characters_dir, _safe_filename(character_name) + ext)


def find_missing_characters(characters: List[str], config: Dict[str, Any]) -> List[str]:
    missing = []
    for name in characters:
        path = _character_png_path(name, config)
        if not os.path.exists(path):
            missing.append(name)
    return missing


def generate_character_rig(character_name: str, config: Dict[str, Any]) -> str:
    """
    Creates assets/characters/<Name>.png using OpenAI Images.
    """
    out_path = _character_png_path(character_name, config)

    client = OpenAI(api_key=config["openai_api_key"])
    model = config.get("openai_image_model", "gpt-image-1")

    style = config.get(
        "openai_character_style",
        "A child-friendly cartoonstyle illustration " 
        "designed with smooth clean line art and soft pastel colors. The character has gentle facial " 
        "features, warm eyes. " 
        "smiling kindly with an open. welcoming expression.  The illustration is 2D digital,"
        " in a children's book aesthetic with smooth-like lines. The colors are soft, pastel tones. The overall" 
        " style is wholesome and comforting, designed to be suitable for a young audience.",
    )

    prompt = (
        f"{style}\n\n"
        f"Character: {character_name}\n"
        "Full-body, front-facing, simple shading.\n"
        "No text, no watermark.\n"
        "Transparent background if possible; otherwise plain white background.\n"
    )

    resp = client.images.generate(
        model=model,
        prompt=prompt,
        size="1024x1536"
    )

    image_b64 = None
    if hasattr(resp, "data") and resp.data:
        item = resp.data[0]
        # Common SDK pattern: resp.data[0].b64_json
        image_b64 = getattr(item, "b64_json", None) or (item.get("b64_json") if isinstance(item, dict) else None)

    if not image_b64:
        raise RuntimeError("No base64 image data found in OpenAI response.")

    _decode_image_to_file(image_b64, out_path)
    return out_path
