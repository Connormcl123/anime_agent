# modules/bible_fetcher.py
import requests
from typing import Dict, Any


def fetch_passage(reference: str, config: Dict[str, Any]) -> Dict[str, str]:
    """
    Fetch canonical Bible text for a reference (e.g., 'Luke 10:30-37').

    Supports:
      - bible-api (no key): https://bible-api.com/

    Returns:
      { "reference": "...", "text": "..." }
    """
    source = (config.get("bible_source") or "bible-api").lower()

    if source == "bible-api":
        # Optional translation support: bible-api.com supports ?translation=kjv (etc.)
        translation = (config.get("bible_translation") or "").strip()
        url = f"https://bible-api.com/{reference}"
        if translation:
            url += f"?translation={translation}"

        r = requests.get(url, timeout=25)
        r.raise_for_status()
        data = r.json()

        ref_out = data.get("reference") or reference
        text_out = (data.get("text") or "").strip()

        # bible-api often includes trailing newlines
        return {"reference": ref_out.strip(), "text": text_out.strip()}

    raise ValueError(f"Unknown bible_source: {source}")
