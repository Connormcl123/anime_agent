# main.py
import json
from modules import story_generator, background_generator, scene_compositor, narration_generator, video_assembler, book_assembler

def main():
    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)

    # 1️⃣ Generate story script (text + scene prompts)
    story_data = story_generator.generate_story(config)
    print("[INFO] Story generated.")

    # 2️⃣ Generate backgrounds from AI
    background_paths = background_generator.generate_backgrounds(story_data['scene_prompts'], config)
    print("[INFO] Backgrounds generated.")

    # 3️⃣ Composite final scene images with character rigs
    scene_paths = scene_compositor.compose_scenes(story_data['scene_prompts'], background_paths, config)
    print("[INFO] Scenes composited.")

    # 4️⃣ Generate narration audio for scenes
    audio_path = narration_generator.generate_narration(story_data['narration_script'], config)
    print("[INFO] Narration audio ready.")

    # 5️⃣ Create animated video
    video_path = video_assembler.assemble_video(scene_paths, audio_path, config)
    print(f"[INFO] Video ready: {video_path}")

    # 6️⃣ Create PDF/EPUB book
    book_path = book_assembler.create_book(story_data['book_text'], scene_paths, config)
    print(f"[INFO] Book ready: {book_path}")

if __name__ == "__main__":
    main()
