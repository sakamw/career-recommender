import json
import os
import re
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

    # Tokenize skills/interests to reduce accidental matches (e.g., "candidate" vs "data")
    tokens = set(re.findall(r"[a-zA-Z]+", skills + " " + interests))

    def any_token(*candidates):
        return any(tok in tokens for tok in candidates)

    # Technical intent: require explicit tech/coding signals, not just "data" or "analytics"
    tech_signals = any_token(
        "python",
        "sql",
        "javascript",
        "java",
        "c++",
        "c",
        "go",
        "rust",
        "model",
        "models",
        "ml",
        "machine",
        "deep",
        "ai",
        "engineer",
        "developer",
        "programming",
        "coding",
        "cloud",
        "aws",
        "azure",
        "gcp",
    )

    base = []

    if any_token("data", "analytics", "analyst", "analysis", "bi") and tech_signals:
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
    if any_token("ml", "machine", "ai", "model", "models", "mlops") and tech_signals:
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
    if any_token("product", "pm", "roadmap"):
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
    if any_token("ops", "mlops", "devops", "platform") and tech_signals:
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
    # Non-technical leaning roles
    if any_token("marketing", "growth", "sales", "business", "partnerships"):
        base.append(
            {
                "career": "AI Solutions / Sales Engineer",
                "score": 7,
                "reason": "Business/market-facing interest detected.",
                "benefits": "Bridge customers and product; strong earning potential.",
                "opportunities": "SaaS presales, partner engineering, enterprise enablement.",
                "sub_careers": ["Customer Engineer", "Partner Engineer"],
            }
        )

    if any_token("business", "analysis", "analyst", "strategy", "consulting", "operations", "process"):
        base.append(
            {
                "career": "Business Analyst / Strategy Analyst",
                "score": 7,
                "reason": "Business/strategy focus detected.",
                "benefits": "Influence decisions with insights; cross-functional impact.",
                "opportunities": "Operations, strategy, PMO, transformation teams.",
                "sub_careers": ["Strategy Associate", "Operations Analyst"],
            }
        )

    if any_token("project", "program", "coordination", "delivery", "management"):
        base.append(
            {
                "career": "Project / Program Coordinator",
                "score": 7,
                "reason": "Project coordination interest detected.",
                "benefits": "Own delivery timelines; cross-functional exposure.",
                "opportunities": "Implementation teams, PMOs, delivery offices.",
                "sub_careers": ["Program Manager", "Implementation Lead"],
            }
        )

    if any_token("design", "ux", "ui", "research", "prototype"):
        base.append(
            {
                "career": "AI UX Designer / Researcher",
                "score": 7,
                "reason": "Design/UX inclination detected.",
                "benefits": "Shape AI experiences and user trust.",
                "opportunities": "Product design teams, research labs, design systems.",
                "sub_careers": ["UX Researcher", "Conversation Designer"],
            }
        )

    if any_token("writing", "content", "communication", "docs", "documentation"):
        base.append(
            {
                "career": "Technical Writer (AI)",
                "score": 7,
                "reason": "Writing/communication strength detected.",
                "benefits": "Explain complex AI topics clearly; flexible work setups.",
                "opportunities": "Product documentation, developer relations content.",
                "sub_careers": ["Developer Advocate (content)", "Docs Specialist"],
            }
        )

    # If still empty, provide a diverse, non-technical set
    if not base or not tech_signals:
        base.extend(
            [
                {
                    "career": "AI Product Specialist",
                    "score": 7,
                    "reason": "General AI interest assumed.",
                    "benefits": "Customer-facing, broad exposure to AI use-cases.",
                    "opportunities": "Solutions engineering, customer success, sales enablement.",
                    "sub_careers": ["Solutions Architect", "AI Implementation Consultant"],
                },
                {
                    "career": "Technical Writer (AI)",
                    "score": 7,
                    "reason": "Communication focus assumed.",
                    "benefits": "Explain complex ideas; flexible/remote friendly.",
                    "opportunities": "Docs teams, DevRel content, education.",
                    "sub_careers": ["Docs Specialist", "Content Strategist"],
                },
                {
                    "career": "AI Project Coordinator",
                    "score": 7,
                    "reason": "Coordination and delivery focus assumed.",
                    "benefits": "Plan and ship; cross-team collaboration.",
                    "opportunities": "Implementation projects, PMO roles.",
                    "sub_careers": ["Program Coordinator", "Implementation Lead"],
                },
                {
                    "career": "Business Analyst",
                    "score": 7,
                    "reason": "Business/operations focus assumed.",
                    "benefits": "Improve processes and decisions; stakeholder-facing.",
                    "opportunities": "Operations, strategy, transformation teams.",
                    "sub_careers": ["Operations Analyst", "Strategy Analyst"],
                },
            ]
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
                if not tech_signals:
                    tech_terms = ("engineer", "scientist", "developer", "ml", "ai", "data")
                    filtered = []
                    for r in recs:
                        career = (r.get("career", "") or "").lower()
                        if any(term in career for term in tech_terms):
                            continue
                        filtered.append(r)
                    recs = filtered or recs  # if filtering wipes out all, keep originals
                if recs:
                    return {"recommendations": recs[:3]}
        except Exception:
            # Fallback to heuristic if parsing fails
            pass

    return {"recommendations": base[:3]}
