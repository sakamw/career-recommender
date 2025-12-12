import json
import os
from typing import Optional

import requests

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
GENAI_MODEL = os.getenv("GENAI_MODEL", "gemini-1.5-flash")
GENAI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GENAI_MODEL}:generateContent"


def _call_genai(prompt: str) -> Optional[str]:
    """
    Calls Google GenAI (Gemini) via REST when GENAI_API_KEY is set.
    Returns generated text or None on failure.
    """
    if not GENAI_API_KEY:
        return None

    try:
        resp = requests.post(
            GENAI_ENDPOINT,
            params={"key": GENAI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates") or []
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts") or []
            if parts and "text" in parts[0]:
                return parts[0]["text"]
    except Exception:
        return None
    return None


def generate_career_recommendation(data: dict) -> dict:
    """
    Uses GenAI when configured; falls back to a local heuristic otherwise.
    Each recommendation includes reason, benefits, opportunities, and sub-careers.
    """
    skills = data.get("skills", "").lower()
    interests = data.get("interests", "").lower()

    base = []
    if "data" in skills:
        base.append(
            {
                "career": "Data Scientist",
                "score": 9,
                "reason": "Strong data interest detected.",
                "benefits": "High demand, versatile across industries, strong pay.",
                "opportunities": "Tech, finance, healthcare, product analytics roles.",
                "sub_careers": ["ML Engineer", "Data Analyst"],
            }
        )
    if "ml" in skills or "machine" in skills:
        base.append(
            {
                "career": "Machine Learning Engineer",
                "score": 8,
                "reason": "Machine learning keywords found.",
                "benefits": "Impactful model deployment, work with modern stacks.",
                "opportunities": "Platform teams, product ML features, AI startups.",
                "sub_careers": ["Applied Scientist", "ML Platform Engineer"],
            }
        )
    if "product" in skills or "product" in interests:
        base.append(
            {
                "career": "AI Product Manager",
                "score": 8,
                "reason": "Product focus noted.",
                "benefits": "Blend of strategy and AI, cross-functional leadership.",
                "opportunities": "AI feature ownership, roadmap planning, GTM roles.",
                "sub_careers": ["AI Product Owner", "Technical Program Manager"],
            }
        )
    if "ops" in skills or "mlops" in skills:
        base.append(
            {
                "career": "MLOps Engineer",
                "score": 7,
                "reason": "Ops/MLops inclination detected.",
                "benefits": "Own reliability and scalability of AI systems.",
                "opportunities": "Infra teams, platform engineering, observability roles.",
                "sub_careers": ["Model Reliability Engineer", "Data Platform Engineer"],
            }
        )
    if not base:
        base.append(
            {
                "career": "AI Product Specialist",
                "score": 7,
                "reason": "General AI interest assumed.",
                "benefits": "Customer-facing, broad exposure to AI use-cases.",
                "opportunities": "Solutions engineering, customer success, sales enablement.",
                "sub_careers": ["Solutions Architect", "AI Implementation Consultant"],
            }
        )

    prompt = (
        "Given this user's background, suggest 3 AI/tech careers as JSON in the shape "
        '{"recommendations":[{"career":"...","score":int,"reason":"...","benefits":"...","opportunities":"...",'
        '"sub_careers":["...","..."]}]}. '
        f"Skills: {skills}. Interests: {interests}. Keep scores 6-10."
    )

    ai_text = _call_genai(prompt)
    if ai_text:
        try:
            parsed = json.loads(ai_text)
            recs = parsed.get("recommendations")
            if isinstance(recs, list) and recs:
                return {"recommendations": recs[:3]}
        except Exception:
            # Fallback to heuristic if parsing fails
            pass

    return {"recommendations": base[:3]}
