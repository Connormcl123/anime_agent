# modules/background_generator.py
import base64
import os
from typing import List, Dict, Any

from openai import OpenAI


def _decode_image_to_file(image_b64: str, out_path: str) -> None:
    data = base64.b64decode(image_b64)
    with open(out_path, "wb") as f:
        f.write(data)


def generate_backgrounds(scene_prompts: List[str], config: Dict[str, Any]) -> List[str]:
    """
    Generates background images using OpenAI Images API.
    Each prompt must describe ONLY backgrounds (no characters).
    """
    os.makedirs("assets/backgrounds", exist_ok=True)

    client = OpenAI(api_key=config["openai_api_key"])
    model = config.get("openai_image_model", "gpt-image-1")

    size = config.get("background_image_size", [1024, 768])
    size_str = f"{size[0]}x{size[1]}"

    global_style = config.get(
        "openai_background_style",
        "Simple, pastel, child-friendly cartoon background, clean shapes, soft lighting, no text, no characters.",
    )

    background_paths: List[str] = []

    for idx, prompt in enumerate(scene_prompts):
        out_path = f"assets/backgrounds/bg_{idx + 1}.png"

        full_prompt = (
            f"{global_style}\n\n"
            f"BACKGROUND DESCRIPTION:\n{prompt}\n\n"
            "Constraints: no words, no captions, no characters, no people."
        )

        try:
            # The OpenAI Python SDK may return different shapes depending on version.
            # We handle the most common base64 response pattern.
            resp = client.images.generate(
                model=model,
                prompt=full_prompt,
                size=size_str,
            )

            # Try to find base64 data
            image_b64 = None
            if hasattr(resp, "data") and resp.data:
                # Newer SDKs typically store b64 in resp.data[0].b64_json
                item = resp.data[0]
                image_b64 = getattr(item, "b64_json", None) or item.get("b64_json") if isinstance(item, dict) else None

            if not image_b64:
                raise RuntimeError("No base64 image data found in OpenAI response.")

            _decode_image_to_file(image_b64, out_path)
            background_paths.append(out_path)

        except Exception as e:
            # Fallback: create a plain white background if generation fails
            print(f"[WARN] Background generation failed for scene {idx + 1}: {e}")
            try:
                from PIL import Image

                w, h = size[0], size[1]
                img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
                img.save(out_path)
                background_paths.append(out_path)
            except Exception as e2:
                print(f"[ERROR] Could not even create fallback background: {e2}")
                # Still append so pipeline length matches
                background_paths.append(out_path)

    return background_paths
