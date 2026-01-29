# main.py
import json
import os
from modules import story_generator, background_generator, scene_compositor, narration_generator, video_assembler, book_assembler

def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)

    # Resolve environment variables if values are placeholders
    for key, value in config.items():
        # If config value exists in env vars, replace with actual
        if isinstance(value, str) and value in os.environ:
            config[key] = os.environ[value]
    return config

def main():
    config = load_config()

    # 1️⃣ Story Generation
    story_data = story_generator.generate_story(config)
    story_generator.save_story(story_data)  # Saves as JSON
    print("[INFO] Story generated.")

    # 2️⃣ Background Generation
    #background_paths = background_generator.generate_backgrounds(story_data['scene_prompts'], config)
    print("[INFO] Backgrounds generated.")

    # 3️⃣ Scene Composition
    #scene_paths = scene_compositor.compose_scenes(story_data['scene_prompts'], background_paths, config)
    print("[INFO] Scenes composited.")

    # 4️⃣ Narration
    #audio_path = narration_generator.generate_narration(story_data['narration_script'], config)
    print("[INFO] Narration audio ready.")

    # 5️⃣ Video Assembly
    #video_path = video_assembler.assemble_video(scene_paths, audio_path, config)
    #print(f"[INFO] Video ready: {video_path}")

    # 6️⃣ Book Assembly
    #book_path = book_assembler.create_book(story_data['book_text'], scene_paths, config)
    #print(f"[INFO] Book ready: {book_path}")

if __name__ == "__main__":
    main()
