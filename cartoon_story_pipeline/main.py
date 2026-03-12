import json
import os
import datetime
import hashlib
from modules import (
    story_generator,
    scene_compositor,
    narration_generator,
    video_assembler,
    book_assembler,
    bible_fetcher,
)

# Optional: only used if auto_generate_missing_characters = true
from modules import character_generator

USED_PASSAGES_PATH = "exports/used_passages.json"


def load_passage_pool(config):
    """
    Loads the curated pool from assets/passages.json by default.
    Falls back to config['passage_pool'] if the file doesn't exist.
    """
    pool_path = config.get("passage_pool_file", "assets/passages.json")
    if os.path.exists(pool_path):
        with open(pool_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        passages = data.get("passages", [])
        return [p.strip() for p in passages if isinstance(p, str) and p.strip()]
    passages = config.get("passage_pool", [])
    return [p.strip() for p in passages if isinstance(p, str) and p.strip()]


def load_used_passages(path=USED_PASSAGES_PATH):
    if not os.path.exists(path):
        return {"used": [], "last_date": None, "last_reference": None}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    used = data.get("used", [])
    if not isinstance(used, list):
        used = []

    return {
        "used": [u.strip() for u in used if isinstance(u, str) and u.strip()],
        "last_date": data.get("last_date"),
        "last_reference": data.get("last_reference"),
    }


def save_used_passages(state, path=USED_PASSAGES_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def pick_passage_no_repeat(config):
    """
    Picks a passage that:
      - does not repeat until pool is exhausted
      - is stable for the same calendar day (reruns pick the same)
      - automatically resets when exhausted (default behavior)
    """
    pool = load_passage_pool(config)
    if not pool:
        return config.get("daily_passage", "Luke 10:30-37")

    state = load_used_passages()
    today = datetime.date.today().isoformat()

    # If rerun same day, return the same passage (stability)
    if state.get("last_date") == today and state.get("last_reference"):
        return state["last_reference"]

    used_set = set(state.get("used", []))

    # Only consider passages still in the pool (if you removed old ones, they won't matter)
    unused = [p for p in pool if p not in used_set]

    # If exhausted, reset or rotate based on config
    if not unused:
        reset_mode = (config.get("exhausted_pool_mode") or "reset").lower()
        if reset_mode == "reset":
            state["used"] = []
            used_set = set()
            unused = pool[:]
        else:
            # Fallback: if not reset, just allow repeats by using full pool
            unused = pool[:]

    # Deterministic pick among unused based on today's date
    h = hashlib.sha256(today.encode("utf-8")).hexdigest()
    idx = int(h[:8], 16) % len(unused)
    chosen = unused[idx]

    # Record
    if chosen not in used_set:
        state["used"].append(chosen)
    state["last_date"] = today
    state["last_reference"] = chosen
    save_used_passages(state)

    return chosen



def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    # Replace any string config value that matches an env var name
    for key, value in config.items():
        if isinstance(value, str) and value in os.environ:
            config[key] = os.environ[value]
    return config


def main():
    config = load_config()

    # 0️⃣ Pull canonical Bible passage text (daily)
    passage_ref = pick_passage_no_repeat(config)
    print(f"[INFO] Selected passage for today: {passage_ref}")

    verse = bible_fetcher.fetch_passage(passage_ref, config)
    print(f"[INFO] Bible passage fetched: {verse['reference']}")

    # 1️⃣ Generate story JSON via OpenAI (now includes characters + scenes)
    story_data = story_generator.generate_story(
        config=config,
        verse_reference=verse["reference"],
        verse_text=verse["text"],
        theme=config.get("daily_theme", ""),
    )
    print("[INFO] Story generated.")

    # Print the cast so you can search your characters folder quickly
    cast = story_data.get("characters", [])
    if cast:
        print("\n[CAST] Characters in story:")
        for c in cast:
            print(f"  - {c}")
    else:
        print("\n[CAST] No characters returned (unexpected).")

    # 1b️⃣ Ensure missing character rigs are generated (optional)
    if config.get("auto_generate_missing_characters", False) and cast:
        missing = character_generator.find_missing_characters(cast, config)
        if missing:
            print("\n[CAST] Missing character rigs detected:")
            for m in missing:
                print(f"  - {m}")
            for m in missing:
                try:
                    out_path = character_generator.generate_character_rig(m, config)
                    print(f"[CAST] Generated rig for '{m}': {out_path}")
                except Exception as e:
                    print(f"[WARN] Failed to generate rig for '{m}': {e}")
        else:
            print("\n[CAST] All character rigs found.")

    # 2️⃣ Compose scenes locally (backgrounds + character rigs)
    #scene_paths = scene_compositor.compose_scenes(story_data, config)
    #print("[INFO] Scenes composited.")

    # 3️⃣ Generate narration audio
    #audio_path = narration_generator.generate_narration(story_data["narration_script"], config)
    #print("[INFO] Narration ready.")

    # 4️⃣ Assemble video
    #video_path = video_assembler.assemble_video(scene_paths, audio_path, config)
    #print(f"[INFO] Video created: {video_path}")

    # 5️⃣ Build PDF book
    #book_path = book_assembler.create_book(story_data["book_text"], scene_paths, config)
    #print(f"[INFO] Book created: {book_path}")


if __name__ == "__main__":
    main()
