import json
import os
from typing import Optional

import requests

HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL", "google/flan-t5-small")
HF_ENDPOINT = f"https://api-inference.huggingface.co/models/{HF_MODEL}"


def _call_hf(prompt: str) -> Optional[str]:
    """
    Calls a free-ish Hugging Face Inference API model when HF_API_KEY is set.
    Returns generated text or None on failure.
    """
    if not HF_API_KEY:
        return None

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 256, "temperature": 0.3},
    }

    try:
        resp = requests.post(HF_ENDPOINT, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0].get("generated_text")
        if isinstance(data, dict):
            return data.get("generated_text") or data.get("text")
    except Exception:
        return None
    return None


def generate_career_recommendation(data: dict) -> dict:
    """
    Sends user questionnaire data to a free (HF) GenAI model when available.
    Falls back to deterministic suggestions otherwise.
    """
    skills = data.get("skills", "").lower()
    interests = data.get("interests", "")

    # Default deterministic suggestions
    base = []
    if "data" in skills:
        base.append({"career": "Data Scientist", "score": 9, "reason": "Strong data interest detected."})
    if "ml" in skills or "machine" in skills:
        base.append({"career": "Machine Learning Engineer", "score": 8, "reason": "Machine learning keywords found."})
    if not base:
        base.append({"career": "AI Product Specialist", "score": 7, "reason": "General AI interest assumed."})

    prompt = (
        "Given this user's background, suggest 3 AI/tech careers as JSON in the shape "
        '{"recommendations":[{"career":"...","score":int,"reason":"..."}]}. '
        f"Skills: {skills}. Interests: {interests}. Keep scores 6-10."
    )
    ai_text = _call_hf(prompt)

    if ai_text:
        try:
            parsed = json.loads(ai_text)
            recs = parsed.get("recommendations")
            if isinstance(recs, list) and recs:
                return {"recommendations": recs[:3]}
        except Exception:
            pass

    return {"recommendations": base[:3]}
