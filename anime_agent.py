# -*- coding: utf-8 -*-
import random
import json
import datetime
import os
import sys
import requests

# ====================================================
# CONFIG: SET THESE IN ENV VARIABLES
# ====================================================

# --- LLM (Scene Discovery + Anime Summarization) ---
AZURE_API_VERSION_LLM = "2025-01-01-preview"   # From your actual endpoint
DEPLOYMENT_ID_LLM_DISCOVER = "gpt-4o-mini"     # EXACT deployment name for discovery
DEPLOYMENT_ID_LLM_SUMMARIZE = "gpt-4o-mini"    # You can use same model for summarization

AZURE_OPENAI_KEY_LLM = os.getenv("AZURE_OPENAI_KEY_LLM")  
AZURE_OPENAI_ENDPOINT_LLM = "https://cmcla-mktvctnp-eastus2.cognitiveservices.azure.com/"  # Base endpoint only


# --- TTS (Narration) ---
AZURE_API_VERSION_TTS = "2025-03-01-preview" 
DEPLOYMENT_ID_TTS = "gpt-4o-mini-tts"

AZURE_OPENAI_KEY_TTS = os.getenv("AZURE_OPENAI_KEY_TTS")  
AZURE_OPENAI_ENDPOINT_TTS = "https://cmcla-mktvctnp-eastus2.cognitiveservices.azure.com/"


# Output location
OUTPUT_DIR = r"output"

# ====================================================
# DISCOVER FAVORITE SCENES
# ====================================================
def discover_favorite_scenes(book_name):
    if not AZURE_OPENAI_KEY_LLM or not AZURE_OPENAI_ENDPOINT_LLM:
        print("[ERROR] Missing LLM credentials. Set AZURE_OPENAI_KEY_LLM and AZURE_OPENAI_ENDPOINT_LLM.")
        sys.exit(1)

    # Always make sure output folder exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    url = f"{AZURE_OPENAI_ENDPOINT_LLM}openai/deployments/{DEPLOYMENT_ID_LLM_DISCOVER}/chat/completions?api-version={AZURE_API_VERSION_LLM}"
    prompt = (
        f"You are a literary expert creating an anime adaptation. "
        f"Analyze the book '{book_name}' and output ONLY valid JSON. "
        f"List the top 10 most beloved, impactful, and emotionally rich moments from the story. "
        f"For each moment:\n"
        f"scene_number (1 to 10)\n"
        f"title (short, dramatic scene name)\n"
        f"description (<= 50 words vivid imagery and emotion visually rich for animation)\n"
        f"No explanations no commentary. Start immediately with {{ and end at final }}."
    )

    payload = {
        "messages": [
            {"role": "system", "content": "Output ONLY valid JSON. No code fences, no extra text."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1200,
        "temperature": 0.7
    }

    headers = {"api-key": AZURE_OPENAI_KEY_LLM, "Content-Type": "application/json"}

    print(f"[AI] Discovering top scenes for '{book_name}'...")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            text = response.json()["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            print("[ERROR] No content in LLM response. Full JSON below:")
            print(json.dumps(response.json(), indent=2))
            raw_path = os.path.join(OUTPUT_DIR, "favorite_scenes_raw.txt")
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(str(response.json()))
            return

        if not text:
            print("[ERROR] Model returned empty output. Full JSON below:")
            print(json.dumps(response.json(), indent=2))
            raw_path = os.path.join(OUTPUT_DIR, "favorite_scenes_raw.txt")
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(str(response.json()))
            return

        # Attempt to clean markdown artifacts before JSON parse
        cleaned_text = text
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.strip("`")   # Remove backticks
            cleaned_text = cleaned_text.replace("json", "").strip()

        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            print("[ERROR] Model did not produce valid JSON. Raw output saved.")
            raw_path = os.path.join(OUTPUT_DIR, "favorite_scenes_raw.txt")
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(text)
            return

        save_path = os.path.join(OUTPUT_DIR, "favorite_scenes.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved favorite scenes to {save_path}")
    else:
        print(f"[ERROR] Azure LLM request failed: {response.status_code} {response.text}")


# ====================================================
# PICK A RANDOM SCENE
# ====================================================
def load_favorite_scenes():
    file = os.path.join(OUTPUT_DIR, "favorite_scenes.json")
    if not os.path.exists(file):
        print("[ERROR] No favorite_scenes.json found. Run 'discover' mode first.")
        sys.exit(1)
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)["scenes"]

def pick_scene_of_the_day():
    return random.choice(load_favorite_scenes())

# ====================================================
# ANIME-STYLE SUMMARIZER USING LLM
# ====================================================
def anime_summarize(scene):
    """Takes a scene from favorite_scenes.json and turns it into anime-style multi-scene JSON."""
    if not AZURE_OPENAI_KEY_LLM or not AZURE_OPENAI_ENDPOINT_LLM:
        print("[ERROR] Missing LLM credentials for summarization.")
        sys.exit(1)

    url = f"{AZURE_OPENAI_ENDPOINT_LLM}openai/deployments/{DEPLOYMENT_ID_LLM_SUMMARIZE}/chat/completions?api-version={AZURE_API_VERSION_LLM}"
    prompt = (
        f"Transform the following book scene into an anime screenplay. "
        f"Scene title: {scene['title']}\n"
        f"Scene description: {scene['description']}\n\n"
        f"Output ONLY valid JSON with:\n"
        f"- 'audio_script': A flowing narration of ~30 seconds matching the anime style.\n"
        f"- 'scenes': List objects with 'time' (e.g., '0-5s'), 'visual' (vivid anime-style description), and 'audio' (matching narration segment)."
    )

    payload = {
        "messages": [
            {"role": "system", "content": "You output anime scene scripts in strict JSON format."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500,
        "temperature": 0.8
    }

    headers = {"api-key": AZURE_OPENAI_KEY_LLM, "Content-Type": "application/json"}

    print(f"[AI] Summarizing scene '{scene['title']}' into anime format...")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        text = response.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print("[ERROR] Summarizer LLM returned invalid JSON.")
            with open(os.path.join(OUTPUT_DIR, "anime_summary_raw.txt"), "w", encoding="utf-8") as f:
                f.write(text)
            return None
    else:
        print(f"[ERROR] Azure LLM request failed: {response.status_code} {response.text}")
        return None

# ====================================================
# SAVE OUTPUT JSON
# ====================================================
def save_output(data, suffix=""):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = datetime.date.today().isoformat() + suffix + ".json"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Output saved to {path}")

# ====================================================
# GENERATE TTS NARRATION
# ====================================================
def generate_tts_azure(audio_text, voice="fable", output_path="narration.mp3"):
    if not AZURE_OPENAI_KEY_TTS or not AZURE_OPENAI_ENDPOINT_TTS:
        print("[ERROR] Missing TTS credentials set AZURE_OPENAI_KEY_TTS and AZURE_OPENAI_ENDPOINT_TTS.")
        sys.exit(1)

    url = f"{AZURE_OPENAI_ENDPOINT_TTS}openai/deployments/{DEPLOYMENT_ID_TTS}/audio/speech?api-version={AZURE_API_VERSION_TTS}"
    payload = {"model": DEPLOYMENT_ID_TTS, "input": audio_text, "voice": voice}
    headers = {"api-key": AZURE_OPENAI_KEY_TTS, "Content-Type": "application/json"}

    print(f"[TTS] Generating narration with voice '{voice}'...")
    r = requests.post(url, headers=headers, json=payload)

    if r.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(r.content)
        print(f"[OK] TTS audio saved to {output_path}")
    else:
        print(f"[ERROR] Azure TTS request failed: {r.status_code} {r.text}")

# ====================================================
# FULL WORKFLOW
# ====================================================
def run_full_workflow():
    print("[RUN] Anime Agent full workflow started")
    scene = pick_scene_of_the_day()
    anime_json = anime_summarize(scene)

    if anime_json:
        save_output(anime_json)
        narration_file = os.path.join(OUTPUT_DIR, datetime.date.today().isoformat() + "_narration.mp3")
        generate_tts_azure(anime_json["audio_script"], voice="fable", output_path=narration_file)
    print("[DONE] Anime Agent workflow finished")

# ====================================================
# ENTRY POINT
# ====================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python anime_agent.py discover \"Book Name\"")
        print("  python anime_agent.py full")
        sys.exit(0)

    mode = sys.argv[1].lower()

    if mode == "discover":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide the book name.")
            sys.exit(1)
        discover_favorite_scenes(" ".join(sys.argv[2:]))

    elif mode == "full":
        run_full_workflow()

    else:
        print(f"[ERROR] Unknown mode: {mode}")
