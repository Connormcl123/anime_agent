# modules/story_generator.py
def generate_story(config):
    """
    Creates a short story script + background descriptions.
    Will integrate OpenAI API in future.
    """
    # TEMP dummy data for development
    return {
        "book_text": [
            "Page 1: Milo, Lena, and Tavi walked along the sunny path.",
            "Page 2: They saw a traveler lying on the road.",
            "Page 3: Others walked past without helping.",
            "Page 4: A kind stranger stopped to help.",
            "Page 5: Everyone learned that kindness matters."
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
