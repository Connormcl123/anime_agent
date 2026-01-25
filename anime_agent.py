# -*- coding: utf-8 -*-
import random
import json
import datetime
import os
import sys
import requests
import time
import glob

# ====================================================
# CONFIG: ENVIRONMENT VARIABLES AND ENDPOINTS
# ====================================================

# --- LLM (Scene Discovery + Anime Summarization) ---
AZURE_API_VERSION_LLM = "2025-01-01-preview"
DEPLOYMENT_ID_LLM_DISCOVER = "gpt-4o-mini"
DEPLOYMENT_ID_LLM_SUMMARIZE = "gpt-4o-mini"

AZURE_OPENAI_KEY_LLM = os.getenv("AZURE_OPENAI_KEY_LLM")
AZURE_OPENAI_ENDPOINT_LLM = "https://cmcla-mktvctnp-eastus2.cognitiveservices.azure.com/"

# --- TTS (Narration) ---
AZURE_API_VERSION_TTS = "2025-03-01-preview"
DEPLOYMENT_ID_TTS = "gpt-4o-mini-tts"

AZURE_OPENAI_KEY_TTS = os.getenv("AZURE_OPENAI_KEY_TTS")
AZURE_OPENAI_ENDPOINT_TTS = "https://cmcla-mktvctnp-eastus2.cognitiveservices.azure.com/"

# --- Image Generation (Azure DALL·E 3) ---
AZURE_API_VERSION_IMAGE = "2024-02-01"
DEPLOYMENT_ID_IMAGE = "dall-e-3"

AZURE_OPENAI_KEY_IMAGE = os.getenv("AZURE_OPENAI_KEY_IMAGE")
AZURE_OPENAI_ENDPOINT_IMAGE = "https://cmcla-mku2j24u-swedencentral.cognitiveservices.azure.com/"

# --- Stable Video Diffusion (Hugging Face) ---
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_URL = "https://api.stability.ai/v1/generation/stable-video-diffusion-v1-1"

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# ====================================================
# DISCOVER FAVORITE SCENES
# ====================================================
def discover_favorite_scenes(book_name):
    if not AZURE_OPENAI_KEY_LLM or not AZURE_OPENAI_ENDPOINT_LLM:
        print("[ERROR] Missing LLM credentials.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    url = f"{AZURE_OPENAI_ENDPOINT_LLM}openai/deployments/{DEPLOYMENT_ID_LLM_DISCOVER}/chat/completions?api-version={AZURE_API_VERSION_LLM}"
    prompt = f"""
    Analyze the book '{book_name}' and output only valid JSON with the following format:
    {{
      "scenes": [
        {{
          "scene_number": 1,
          "title": "...",
          "description": "..."
        }}
      ]
    }}
    Ensure 'scenes' is the top-level key, exactly as shown. No extra text outside JSON.
    """

    payload = {
        "messages": [
            {"role": "system", "content": "Output ONLY valid JSON starting with { \"scenes\": [ and ending with ] }"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1200,
        "temperature": 0.7
    }

    headers = {"api-key": AZURE_OPENAI_KEY_LLM, "Content-Type": "application/json"}
    print(f"[AI] Discovering top scenes for '{book_name}'...")
    r = requests.post(url, headers=headers, json=payload)

    if r.status_code == 200:
        text = r.json()["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.strip("`").replace("json", "").strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print("[ERROR] Invalid JSON  saved raw.")
            with open(os.path.join(OUTPUT_DIR, "favorite_scenes_raw.txt"), "w", encoding="utf-8") as f:
                f.write(text)
            return
        save_path = os.path.join(OUTPUT_DIR, "favorite_scenes.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved favorite scenes to {save_path}")
    else:
        print(f"[ERROR] Azure LLM failed: {r.status_code} {r.text}")

# ====================================================
# LOAD FAVORITE SCENES
# ====================================================
def load_favorite_scenes():
    path = os.path.join(OUTPUT_DIR, "favorite_scenes.json")
    if not os.path.exists(path):
        print("[ERROR] No favorite_scenes.json found. Run discover mode first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "scenes" in data:
        return data["scenes"]
    elif isinstance(data, list):
        return data
    else:
        print("[ERROR] favorite_scenes.json invalid format.")
        sys.exit(1)

def pick_scene_of_the_day():
    return random.choice(load_favorite_scenes())

# ====================================================
# ANIME SUMMARIZATION
# ====================================================
def anime_summarize(scene, book_context=None):
    if not AZURE_OPENAI_KEY_LLM or not AZURE_OPENAI_ENDPOINT_LLM:
        print("[ERROR] Missing LLM credentials.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    url = f"{AZURE_OPENAI_ENDPOINT_LLM}openai/deployments/{DEPLOYMENT_ID_LLM_SUMMARIZE}/chat/completions?api-version={AZURE_API_VERSION_LLM}"

    context_section = f"\nBOOK CONTEXT:\n{book_context}\n" if book_context else ""
    prompt = f"""
    Write an anime-style screenplay for the following scene description.
    Include accurate character appearances, personalities, and background from book context.
    SCENE TITLE: {scene['title']}
    SCENE DESCRIPTION: {scene['description']}
    {context_section}
    Output ONLY valid JSON with:
    {{
      "audio_script": "...",
      "scenes": [
        {{ "time": "0-5s", "visual": "...", "audio": "..." }}
      ]
    }}
    No extra commentary or text outside the JSON.
    """

    payload = {
        "messages": [
            {"role": "system", "content": "Output anime scripts in strict JSON format."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.8
    }

    headers = {"api-key": AZURE_OPENAI_KEY_LLM, "Content-Type": "application/json"}
    print(f"[AI] Summarizing scene '{scene['title']}'...")
    r = requests.post(url, headers=headers, json=payload)

    if r.status_code == 200:
        text = r.json()["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.strip("`").replace("json", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print("[ERROR] Invalid anime script JSON saved raw.")
            with open(os.path.join(OUTPUT_DIR, "anime_summary_raw.txt"), "w", encoding="utf-8") as f:
                f.write(text)
            return None
    else:
        print(f"[ERROR] Azure LLM failed: {r.status_code} {r.text}")
        return None

# ====================================================
# SAVE OUTPUT
# ====================================================
def save_output(data, suffix=""):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = datetime.date.today().isoformat() + suffix + ".json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Output saved to {filepath}")

# ====================================================
# TTS GENERATION
# ====================================================
def generate_tts_azure(audio_text, voice="fable", output_path="narration.mp3"):
    if not AZURE_OPENAI_KEY_TTS or not AZURE_OPENAI_ENDPOINT_TTS:
        print("[ERROR] Missing TTS credentials.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
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
        print(f"[ERROR] Azure TTS failed: {r.status_code} {r.text}")

# ====================================================
# IMAGE GENERATION (Azure DALL·E 3)
# ====================================================
def generate_anime_frame(scene_visual, output_filename):
    if not AZURE_OPENAI_KEY_IMAGE or not AZURE_OPENAI_ENDPOINT_IMAGE:
        print("[ERROR] Missing Image credentials.")
        return

    url = f"{AZURE_OPENAI_ENDPOINT_IMAGE}openai/deployments/{DEPLOYMENT_ID_IMAGE}/images/generations?api-version={AZURE_API_VERSION_IMAGE}"
    styled_prompt = f"{scene_visual}, anime style, highly detailed, vibrant colors, cinematic lighting, 4k resolution"
    payload = {"prompt": styled_prompt, "size": "1024x1024", "n": 1}
    headers = {"api-key": AZURE_OPENAI_KEY_IMAGE, "Content-Type": "application/json"}

    print(f"[IMG] Generating image: {scene_visual}")
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code == 200:
        try:
            result = r.json()
            image_url = result["data"][0]["url"]
            img_data = requests.get(image_url).content
            with open(output_filename, "wb") as f:
                f.write(img_data)
            print(f"[OK] Image saved: {output_filename}")
        except Exception as e:
            print(f"[ERROR] Saving image failed: {e}")
    else:
        print(f"[ERROR] Image failed: {r.status_code} {r.text}")

# ====================================================
# SVD VIDEO GENERATION (Hugging Face)
# ====================================================
def svd_image_to_video(image_path, output_path, motion="camera pan", frames=14, scale=512):
    if not HUGGINGFACE_API_KEY:
        print("[ERROR] Missing Hugging Face API key.")
        return

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    files = {"image": open(image_path, "rb")}
    data = {"frames": frames, "size": scale, "motion": motion}

    print(f"[SVD] Converting {image_path} to video...")
    response = requests.post(HUGGINGFACE_API_URL, headers=headers, files=files, data=data)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"[OK] Video saved: {output_path}")
    else:
        print(f"[ERROR] SVD failed {response.status_code}: {response.text}")

# ====================================================
# FRAME & VIDEO GENERATION WRAPPERS
# ====================================================
def generate_all_frames(script_path):
    with open(script_path, "r", encoding="utf-8") as f:
        anime_data = json.load(f)
    frames_dir = os.path.join(OUTPUT_DIR, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    for idx, scene in enumerate(anime_data["scenes"], start=1):
        visual_prompt = scene["visual"]
        output_file = os.path.join(frames_dir, f"scene_{idx}.png")
        generate_anime_frame(visual_prompt, output_file)
        print("[WAIT] Pausing to respect Azure rate limits...")
        time.sleep(25)  # Rate limit pause

def svd_all_frames_to_videos():
    frames_dir = os.path.join(OUTPUT_DIR, "frames")
    videos_dir = os.path.join(OUTPUT_DIR, "videos")
    os.makedirs(videos_dir, exist_ok=True)
    for frame_path in sorted(glob.glob(os.path.join(frames_dir, "*.png"))):
        base_name = os.path.splitext(os.path.basename(frame_path))[0]
        video_path = os.path.join(videos_dir, f"{base_name}.mp4")
        svd_image_to_video(frame_path, video_path)

# ====================================================
# FULL WORKFLOW
# ====================================================
def run_full_workflow():
    print("[RUN] Anime Agent started")
    scene = pick_scene_of_the_day()

    book_context = """Main Characters:
    - Violet Sorrengail: Petite, silver hair, violet eyes, physically frail but highly intelligent.
    - Xaden Riorson: Tall, dark hair, broad shoulders, gray eyes, confident leader.
    World: Dragon-riding war college, stone fortresses, mountainous terrain, stormy skies.
    Tone: Intense, high stakes, romantic tension.
    """

    anime_json = anime_summarize(scene, book_context=book_context)
    if anime_json:
        script_filename = datetime.date.today().isoformat() + "_anime_script.json"
        script_path = os.path.join(OUTPUT_DIR, script_filename)
        save_output(anime_json, suffix="_anime_script")

        narration_file = os.path.join(OUTPUT_DIR, datetime.date.today().isoformat() + "_narration.mp3")
        generate_tts_azure(anime_json["audio_script"], voice="fable", output_path=narration_file)

        generate_all_frames(script_path)
        svd_all_frames_to_videos()

    print("[DONE] Anime Agent finished")

# ====================================================
# ENTRY POINT
# ====================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:\n  python anime_agent.py discover \"Book Name\"\n  python anime_agent.py full")
        sys.exit(0)

    mode = sys.argv[1].lower()
    if mode == "discover":
        if len(sys.argv) < 3:
            print("[ERROR] Provide book name.")
            sys.exit(1)
        discover_favorite_scenes(" ".join(sys.argv[2:]))
    elif mode == "full":
        run_full_workflow()
    else:
        print(f"[ERROR] Unknown mode: {mode}")
