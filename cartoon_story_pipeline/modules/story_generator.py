# modules/story_generator.py
import json
import os
from openai import OpenAI

def generate_story(config):
    """
    Generates a child-friendly story structure using the new OpenAI Python API (>=1.0.0).
    """
    try:
        client = OpenAI(api_key=config["openai_api_key"])

        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Could also use "gpt-4o" or "gpt-3.5-turbo"
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that writes gentle, child-friendly cartoon religious short stories "
                        "for ages 4-7 with recurring characters: Jesus (wise guide), God (all knowing being), "
                        "and various other religious characters. Stories should be exerted from the Bible but "
                        "can be rephrased to be positive, kind, and safe. The overall theme and message from the Bible verses "
                        "being reimagined for young children should be the main objective. The stories however can be reinterpreted "
                        "for children audiences. "
                        "Output in JSON format with keys: book_text, narration_script, scene_prompts."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate a short story (~10 pages) themed around '{config.get('daily_theme')}'. "
                        "Ensure each book page has 1-3 sentences. And link the Bible verse the story is linked to."
                        "Generate a short narration_script for video (~5 minutes). "
                        "scene_prompts should be vivid background descriptions without drawing characters."
                    )
                }
            ],
            temperature=0.7
        )

        # Parse JSON response from GPT
        story_text = completion.choices[0].message.content.strip()
        story_data = json.loads(story_text)

    except json.JSONDecodeError:
        print("[ERROR] OpenAI output was not valid JSON. Falling back to placeholder.")
        story_data = {
            "book_text": [
                "Milo, Lena, and Tavi walked along the sunny path.",
                "They saw a traveler lying on the road.",
                "Others passed without helping.",
                "A kind stranger stopped to help.",
                "Everyone learned that kindness matters."
            ],
            "narration_script": "Once upon a time, Milo, Lena, and Tavi were on a sunny path...",
            "scene_prompts": [
                "Sunny countryside path with trees and flowers",
                "Dusty road with a hurt traveler under the sun",
                "Two travelers walking past and looking away",
                "A friendly stranger helping the traveler",
                "Milo, Lena, and Tavi smiling as they walk away"
            ]
        }

    except Exception as e:
        print("[ERROR] Failed to generate story:", e)
        # Fallback to placeholders so the pipeline can still run
        story_data = {
            "book_text": [
                "Milo, Lena, and Tavi walked along the sunny path.",
                "They saw a traveler lying on the road.",
                "Others passed without helping.",
                "A kind stranger stopped to help.",
                "Everyone learned that kindness matters."
            ],
            "narration_script": "Once upon a time, Milo, Lena, and Tavi were on a sunny path...",
            "scene_prompts": [
                "Sunny countryside path with trees and flowers",
                "Dusty road with a hurt traveler under the sun",
                "Two travelers walking past and looking away",
                "A friendly stranger helping the traveler",
                "Milo, Lena, and Tavi smiling as they walk away"
            ]
        }

    return story_data


def save_story(story_data, filename="exports/story_data.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(story_data, f, indent=4, ensure_ascii=False)
