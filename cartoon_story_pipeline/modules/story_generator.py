# modules/story_generator.py
import json
import os
from openai import OpenAI

def generate_story(config):
    """
    Generates a child-friendly story structure as valid JSON every time.
    Uses OpenAI API with enforced JSON mode.
    """
    client = OpenAI(api_key=config["openai_api_key"])

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                         "You are an assistant that writes gentle, child-friendly cartoon religious short stories "
                        "for ages 4-7 with recurring characters from the Bible: Jesus, God (all knowing being), "
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
                        f"Generate a short story (~10 pages) themed around a verse from the Bible. "
                        "Ensure each book page has 1-3 sentences. Provide the Bible verse that relates to the story."
                        "Generate a short narration_script for video (~5 minutes). "
                        "scene_prompts should be vivid background descriptions without drawing characters."
                    )
                }
            ],
            temperature=0.7,
            response_format={ "type": "json_object" }  # Force JSON output
        )

        story_text = completion.choices[0].message.content.strip()
        story_data = json.loads(story_text)

    except json.JSONDecodeError:
        print("[ERROR] GPT returned invalid JSON. Attempting auto-repair...")
        try:
            # Try to fix common JSON issues
            repaired = story_text.strip("` \n\t")
            repaired = repaired[repaired.find("{") : repaired.rfind("}") + 1]  # Extract JSON section
            story_data = json.loads(repaired)
        except Exception:
            print("[ERROR] Could not repair JSON. Using fallback story.")
            story_data = fallback_story()

    except Exception as e:
        print("[ERROR] OpenAI call failed:", e)
        story_data = fallback_story()

    return story_data


def fallback_story():
    """Return a default story if the API fails."""
    return {
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


def save_story(story_data, filename="exports/story_data.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(story_data, f, indent=4, ensure_ascii=False)

