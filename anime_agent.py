import random
import json
import datetime
import os
import sys
import requests

# === CONFIG ===
BOOK_FILE = r"C:\anime_agent\book.txt"  # optional if you want raw text source
OUTPUT_DIR = r"C:\anime_agent\output"   # where files will be saved

# ----------------------------------------------------
# STEP 1: AI-powered Favorite Scene Discovery
# ----------------------------------------------------
def discover_favorite_scenes(book_name):
    """
    Uses Azure OpenAI to list top 10 favorite moments from the book.
    Stores them locally as favorite_scenes.json in OUTPUT_DIR.
    """
    api_key = os.getenv("4h0aYHtNIA8z8IEYDpvUJ9TQmt9Qp7kXWhBGtLKl34WMTnD5VtpwJQQJ99CAACYeBjFXJ3w3AAABACOG6c7M")
    endpoint = os.getenv("https://bookanime-openai.openai.azure.com/")

    if not api_key or not endpoint:
        print("[ERROR] Azure OpenAI key and/or endpoint not set. Use setx to configure them.")
        sys.exit(1)

    deployment_id = "gpt-4o-mini"  # Change to your Azure deployment name for GPT model
    url = f"{endpoint}openai/deployments/{deployment_id}/chat/completions"

    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a literary analyst who identifies the most beloved, impactful, and dramatic moments from popular books."
            },
            {
                "role": "user",
                "content": f"List the top 10 favorite moments in the book '{book_name}'. "
                           f"For each, include scene_number, title, and a vivid one-sentence description. "
                           f"Format as JSON with a top-level key 'scenes', which is a list of scene objects."
            }
        ],
        "max_tokens": 800
    }

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }

    print(f"[AI] Finding top scenes for: {book_name}...")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        fav_scenes_text = response.json()["choices"][0]["message"]["content"]
        try:
            fav_scenes_data = json.loads(fav_scenes_text)
        except json.JSONDecodeError:
            print("[WARN] AI did not return perfect JSON, wrapping it manually.")
            fav_scenes_data = {"scenes": [{"scene_number": i+1, "title": s, "description": s} 
                                for i, s in enumerate(fav_scenes_text.split("\n")) if s.strip()]}

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        save_path = os.path.join(OUTPUT_DIR, "favorite_scenes.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(fav_scenes_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved favorite scenes to {save_path}")
    else:
        print(f"[ERROR] Azure LLM request failed: {response.status_code} {response.text}")


# ----------------------------------------------------
# STEP 2: Load stored favorite scenes
# ----------------------------------------------------
def load_favorite_scenes():
    fav_file = os.path.join(OUTPUT_DIR, "favorite_scenes.json")
    if not os.path.exists(fav_file):
        print("[ERROR] No favorite_scenes.json found. Run 'discover' mode first.")
        sys.exit(1)
    with open(fav_file, "r", encoding="utf-8") as f:
        fav_data = json.load(f)
    return fav_data["scenes"]

def pick_scene_of_the_day():
    favorites = load_favorite_scenes()
    return random.choice(favorites)


# ----------------------------------------------------
# STEP 3: Anime-style summarization (Mock for now)
# ----------------------------------------------------
def anime_summarize(scene_description):
    """
    Mock function to generate anime JSON from a scene description.
    Replace later with a real GPT call for anime-styled screenplay output.
    """
    summary_json = {
        "audio_script": f"{scene_description} (Anime-styled dramatic narration...)",
        "scenes": [
            {
                "time": "0-5s",
                "visual": "Cherry blossom petals falling in slow motion...",
                "audio": scene_description
            },
            {
                "time": "5-10s",
                "visual": "Closeup of character with emotional tear in eye...",
                "audio": "(Emotional pause)"
            }
        ]
    }
    return summary_json


# ----------------------------------------------------
# STEP 4: Save JSON output
# ----------------------------------------------------
def save_output(data, suffix=""):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = datetime.date.today().isoformat() + suffix + ".json"
    file_path = os.path.join(OUTPUT_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Output saved to {file_path}")


# ----------------------------------------------------
# STEP 5: Azure OpenAI TTS
# ----------------------------------------------------
def generate_tts_azure(audio_text, voice_name="fable", output_path="narration.mp3"):
    api_key = os.getenv("4h0aYHtNIA8z8IEYDpvUJ9TQmt9Qp7kXWhBGtLKl34WMTnD5VtpwJQQJ99CAACYeBjFXJ3w3AAABACOG6c7M")
    endpoint = os.getenv("https://bookanime-openai.openai.azure.com/")

    if not api_key or not endpoint:
        print("[ERROR] Azure OpenAI API key/endpoint not set.")
        sys.exit(1)

    deployment_id = "tts-1"  # Change if your TTS deployment has a different name
    url = f"{endpoint}openai/deployments/{deployment_id}/audio/speech"

    payload = {
        "model": deployment_id,
        "input": audio_text,
        "voice": voice_name
    }

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }

    print(f"[TTS] Generating audio with voice '{voice_name}'...")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"[OK] TTS audio saved to {output_path}")
    else:
        print(f"[ERROR] TTS request failed: {response.status_code} {response.text}")


# ----------------------------------------------------
# STEP 6: Modes
# ----------------------------------------------------
def run_full_workflow():
    print("[RUN] Anime Agent full workflow started")
    scene = pick_scene_of_the_day()
    scene_desc = scene["description"]
    anime_json = anime_summarize(scene_desc)
    save_output(anime_json)

    # Generate TTS narration
    narration_text = anime_json["audio_script"]
    narration_filename = datetime.date.today().isoformat() + "_narration.mp3"
    narration_path = os.path.join(OUTPUT_DIR, narration_filename)
    generate_tts_azure(narration_text, voice_name="fable", output_path=narration_path)

    print("[DONE] Anime Agent full workflow finished")


def run_llm_test():
    print("[RUN] Anime Agent LLM test")
    sample_text = "The moonlight shimmered on the blade as the hero prepared for battle."
    anime_json = anime_summarize(sample_text)
    print(json.dumps(anime_json, indent=2, ensure_ascii=False))
    print("[DONE] LLM test run finished")


# ----------------------------------------------------
# MAIN ENTRY
# ----------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python anime_agent.py discover \"Book Name\"   # Find and store top scenes")
        print("  python anime_agent.py full                    # Run full daily workflow")
        print("  python anime_agent.py llmtest                 # Test summarizer only")
        sys.exit(0)

    mode = sys.argv[1].lower()

    if mode == "discover":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide the book name.")
            sys.exit(1)
        book_name = " ".join(sys.argv[2:])
        discover_favorite_scenes(book_name)

    elif mode == "full":
        run_full_workflow()

    elif mode == "llmtest":
        run_llm_test()

    else:
        print(f"[ERROR] Unknown mode: {mode}")
