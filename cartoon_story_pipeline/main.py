import json
import os
from modules import story_generator, scene_compositor, narration_generator, video_assembler, book_assembler

def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
    for key, value in config.items():
        if isinstance(value, str) and value in os.environ:
            config[key] = os.environ[value]
    return config

def main():
    config = load_config()

    # 1️⃣ Generate story as valid JSON via OpenAI
    story_data = story_generator.generate_story(config)
    print("[INFO] Story generated.")

    # 2️⃣ Compose minimalist scenes locally with background artifacts + character rigs
    scene_paths = scene_compositor.compose_scenes(story_data["scene_prompts"], config)
    print("[INFO] Scenes composited.")

    # 3️⃣ Generate narration audio
    audio_path = narration_generator.generate_narration(story_data["narration_script"], config)
    print("[INFO] Narration ready.")

    # 4️⃣ Assemble video
    video_path = video_assembler.assemble_video(scene_paths, audio_path, config)
    print(f"[INFO] Video created: {video_path}")

    # 5️⃣ Build PDF book
    book_path = book_assembler.create_book(story_data["book_text"], scene_paths, config)
    print(f"[INFO] Book created: {book_path}")

if __name__ == "__main__":
    main()
