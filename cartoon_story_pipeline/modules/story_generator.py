# modules/story_generator.py
import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI


REQUIRED_TOP_KEYS = [
    "verse_reference",
    "verse_text",
    "moral",
    "book_text",
    "narration_script",
    "characters",
    "scenes",
    # Backward compatibility:
    "scene_prompts",
]


def _safe_json_load(text: str) -> Dict[str, Any]:
    """
    Loads JSON from model output with basic repair attempts.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to strip code fences and extract the first {...} block
        cleaned = text.strip().strip("`")
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def _normalize_story(data: Dict[str, Any], verse_reference: str, verse_text: str) -> Dict[str, Any]:
    """
    Ensures required keys exist and data types are correct.
    Also builds backward-compatible `scene_prompts`.
    """
    # Defaults
    data.setdefault("verse_reference", verse_reference)
    data.setdefault("verse_text", verse_text)
    data.setdefault("moral", "")

    # book_text
    if not isinstance(data.get("book_text"), list):
        data["book_text"] = []
    data["book_text"] = [str(x) for x in data["book_text"]]

    # narration_script
    if not isinstance(data.get("narration_script"), str):
        data["narration_script"] = str(data.get("narration_script", ""))

    # characters
    if not isinstance(data.get("characters"), list):
        data["characters"] = []
    data["characters"] = [str(x).strip() for x in data["characters"] if str(x).strip()]

    # scenes
    scenes = data.get("scenes")
    if not isinstance(scenes, list):
        scenes = []

    normalized_scenes: List[Dict[str, Any]] = []
    for i, s in enumerate(scenes, start=1):
        if not isinstance(s, dict):
            continue
        prompt = str(s.get("prompt", "")).strip()
        chars = s.get("characters_in_scene", [])
        if not isinstance(chars, list):
            chars = []
        chars = [str(c).strip() for c in chars if str(c).strip()]
        sid = s.get("id", i)
        try:
            sid = int(sid)
        except Exception:
            sid = i
        normalized_scenes.append(
            {
                "id": sid,
                "prompt": prompt,
                "characters_in_scene": chars,
            }
        )

    # If no scenes returned, create a minimal fallback based on book_text length
    if not normalized_scenes and data["book_text"]:
        for i, _ in enumerate(data["book_text"][:8], start=1):
            normalized_scenes.append(
                {
                    "id": i,
                    "prompt": "Simple pastel countryside background, soft lighting, no text, no characters.",
                    "characters_in_scene": data["characters"][:2] if data["characters"] else [],
                }
            )

    data["scenes"] = normalized_scenes

    # Backward compatibility: scene_prompts is just the prompts array
    data["scene_prompts"] = [s["prompt"] for s in data["scenes"]]

    # Ensure required keys exist
    for k in REQUIRED_TOP_KEYS:
        data.setdefault(k, [] if k in ("book_text", "characters", "scenes", "scene_prompts") else "")

    return data


def generate_story(
    config,
    verse_reference: str,
    verse_text: str,
    theme: str = "",
):
    """
    Generates a child-friendly paraphrased story
    based ONLY on the provided Bible verse text.
    """

    client = OpenAI(
        api_key=config["openai_api_key"],
        timeout=60.0,
        max_retries=3
    )

    model = config.get("openai_text_model", "gpt-4o-mini")

    system_prompt = """
You are a gentle children's Bible storyteller.

Your task:
- Retell the provided Bible passage in a condensed, paraphrased, story-like way.
- The story must be appropriate for ages 4–7.
- Avoid scary, violent, or graphic details.
- If the original passage contains harm, conflict, or danger,
  soften it into a safe and uplifting version.
- Emphasize kindness, love, faith, bravery, forgiveness, or other positive morals.
- Do NOT add new scripture text.
- Do NOT quote large portions of the original verse.
- The verse_text field in the output must match EXACTLY the input text.
- All scene prompts must describe ONLY backgrounds (no characters, no text).
- Return a valid JSON object only.
"""

    user_prompt = f"""
Theme (optional): {theme}

Bible Reference: {verse_reference}

Bible Passage Text (use only this as source material):
{verse_text}

Create a condensed, child-friendly story retelling this passage.

Return ONE JSON object with the following keys:

1) verse_reference (string)
2) verse_text (string — must match input exactly)
3) moral (string — 1-2 short sentences for children)
4) book_text (array of 6–12 short story pages, 3-4 sentences each)
5) narration_script (string, 60–120 seconds spoken)
6) characters (array of unique character names used in story)
7) scenes (array of 6–10 objects):
   - id (integer)
   - prompt (background-only description)
   - characters_in_scene (array of character names)
"""

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            response_format={"type": "json_object"},
        )

        story_text = completion.choices[0].message.content.strip()
        data = json.loads(story_text)

        # Safety: force verse_text to remain canonical
        data["verse_reference"] = verse_reference
        data["verse_text"] = verse_text

        # Backward compatibility
        data["scene_prompts"] = [s["prompt"] for s in data.get("scenes", [])]

        return data

    except Exception as e:
        print("[ERROR] OpenAI story generation failed:", e)
        return fallback_story(verse_reference, verse_text)


def fallback_story(verse_reference: str, verse_text: str) -> Dict[str, Any]:
    return {
        "verse_reference": verse_reference,
        "verse_text": verse_text,
        "moral": "God wants us to be kind and help others when they need us.",
        "book_text": [
            "One day, someone needed help on the road.",
            "Some people walked by and did not stop.",
            "Then a kind person stopped to help.",
            "They shared care, time, and kindness.",
            "Everyone learned that helping others is the right choice."
        ],
        "narration_script": "Once upon a time, someone needed help on the road. Some people walked by, but one kind person stopped to help. God smiles when we love our neighbors.",
        "characters": ["Jesus", "Traveler", "Kind Helper"],
        "scenes": [
            {"id": 1, "prompt": "Sunny road in the countryside with gentle hills and trees, pastel colors, no text.", "characters_in_scene": ["Traveler"]},
            {"id": 2, "prompt": "A quiet path with footprints and soft sunlight through trees, pastel colors, no text.", "characters_in_scene": ["Traveler"]},
            {"id": 3, "prompt": "Roadside with a small shaded area and a simple cart path, pastel colors, no text.", "characters_in_scene": ["Kind Helper", "Traveler"]},
            {"id": 4, "prompt": "Simple village edge with small houses far away, warm sunset light, pastel colors, no text.", "characters_in_scene": ["Kind Helper", "Traveler"]},
            {"id": 5, "prompt": "Peaceful walkway with flowers and soft sky, pastel colors, no text.", "characters_in_scene": ["Jesus"]},
        ],
        "scene_prompts": [],
    }


def save_story(story_data: Dict[str, Any], filename: str = "exports/story_data.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(story_data, f, indent=4, ensure_ascii=False)
