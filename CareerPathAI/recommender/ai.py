import json
import os
import re
from typing import Optional

import requests

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
GENAI_MODEL = os.getenv("GENAI_MODEL", "gemini-1.5-flash")
GENAI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GENAI_MODEL}:generateContent"

# Bump this when you change the shape/intent of the prompt.
PROMPT_VERSION = "v2-action-plan-1"


def _default_action_plan_for(career_name: str) -> dict:
    """Reasonable, curated defaults (used for fallback and to fill AI gaps)."""

    name = (career_name or "").lower()

    # NOTE: keep URLs fairly stable / broadly useful.
    if "data scientist" in name:
        return {
            "getting_started": [
                "Refresh Python + NumPy/Pandas and basic statistics.",
                "Learn SQL for analytics (joins, aggregations, window functions).",
                "Build 1–2 small end-to-end projects (EDA → model → write-up).",
                "Publish your work (GitHub + short portfolio page).",
            ],
            "resources": [
                {"title": "Kaggle Learn (Python / ML / SQL)", "url": "https://www.kaggle.com/learn"},
                {"title": "scikit-learn User Guide", "url": "https://scikit-learn.org/stable/user_guide.html"},
                {"title": "Pandas Documentation", "url": "https://pandas.pydata.org/docs/"},
                {"title": "SQLBolt (SQL basics)", "url": "https://sqlbolt.com/"},
            ],
            "interview_prep": [
                "Practice SQL questions (joins, CTEs, window functions) and explain tradeoffs.",
                "Review statistics (distributions, bias/variance, A/B testing basics).",
                "Prepare 2–3 project stories: problem → approach → result → what you'd improve.",
            ],
            "how_to_apply": [
                "Tailor your resume to highlight measurable impact and relevant tools.",
                "Apply to roles that match your current level (intern/junior/associate) and iterate weekly.",
                "Network: ask for referrals + informational chats; share one project post.",
            ],
        }

    if "machine learning engineer" in name or ("ml" in name and "engineer" in name):
        return {
            "getting_started": [
                "Pick a core stack: Python + PyTorch or TensorFlow.",
                "Practice training + evaluating models (metrics, overfitting, data leakage).",
                "Learn deployment basics (Docker, REST APIs) and CI for ML.",
                "Build a small "
                "model-serving demo (API + simple UI) and document it well.",
            ],
            "resources": [
                {"title": "Google ML Crash Course", "url": "https://developers.google.com/machine-learning/crash-course"},
                {"title": "PyTorch Tutorials", "url": "https://pytorch.org/tutorials/"},
                {"title": "TensorFlow Tutorials", "url": "https://www.tensorflow.org/tutorials"},
                {"title": "Docker Getting Started", "url": "https://docs.docker.com/get-started/"},
            ],
            "interview_prep": [
                "Brush up on fundamentals: bias/variance, regularization, metrics, leakage.",
                "Practice coding (arrays/strings, data structures) and basic system design.",
                "Be ready to discuss how you'd debug a model in production (data drift, monitoring).",
            ],
            "how_to_apply": [
                "Show evidence of shipping: a repo with tests, Dockerfile, and a working demo.",
                "Target teams that need applied ML (recommendations, NLP, forecasting) and match your projects.",
                "Write a short 'model card' / README to stand out.",
            ],
        }

    if "mlops" in name:
        return {
            "getting_started": [
                "Learn Docker + basic Linux + CI/CD concepts.",
                "Understand experiment tracking and model registries.",
                "Practice serving/monitoring models (logging, metrics, drift).",
                "Build a minimal pipeline: train → package → deploy → monitor.",
            ],
            "resources": [
                {"title": "Docker Getting Started", "url": "https://docs.docker.com/get-started/"},
                {"title": "Kubernetes Basics", "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/"},
                {"title": "MLflow", "url": "https://mlflow.org/"},
            ],
            "interview_prep": [
                "Know reliability basics: SLOs, incidents, rollbacks, capacity planning.",
                "Explain an end-to-end ML system and where failures happen.",
                "Be ready for infra questions (containers, networking basics, observability).",
            ],
            "how_to_apply": [
                "Highlight infrastructure wins (automation, cost, reliability) and tooling.",
                "Contribute to an open-source MLOps tool or write a deployment tutorial.",
            ],
        }

    if "product" in name and ("pm" in name or "manager" in name):
        return {
            "getting_started": [
                "Learn the AI product lifecycle (data → model → evaluation → launch).",
                "Practice writing PRDs and defining success metrics.",
                "Study common AI constraints (latency, cost, safety, evaluation).",
                "Build a simple demo product and write a one-page strategy.",
            ],
            "resources": [
                {"title": "Google: Product Management resources", "url": "https://grow.google/certificates/project-management/"},
                {"title": "OpenAI Cookbook (prompting/examples)", "url": "https://cookbook.openai.com/"},
            ],
            "interview_prep": [
                "Practice product sense: user pain → solution → tradeoffs → success metrics.",
                "Prepare stories about alignment, prioritization, and stakeholder management.",
                "Know AI evaluation concepts (quality metrics, human eval, guardrails).",
            ],
            "how_to_apply": [
                "Build a portfolio: 2–3 mock PRDs + one shipped demo.",
                "Tailor your resume around impact, leadership, and decision-making.",
            ],
        }

    if "writer" in name:
        return {
            "getting_started": [
                "Write 3–5 short technical articles explaining AI concepts clearly.",
                "Practice docs structure: quickstart, reference, troubleshooting.",
                "Build a small sample docs site (Markdown + static generator).",
            ],
            "resources": [
                {"title": "Google Developer Documentation Style Guide", "url": "https://developers.google.com/style"},
                {"title": "Write the Docs (community)", "url": "https://www.writethedocs.org/"},
            ],
            "interview_prep": [
                "Expect a writing test: clarity, structure, correctness.",
                "Be ready to talk about information architecture and audience analysis.",
            ],
            "how_to_apply": [
                "Create a portfolio page with writing samples and before/after doc edits.",
                "Apply to roles in DevRel/docs teams and emphasize collaboration with engineers.",
            ],
        }

    # Generic fallback
    return {
        "getting_started": [
            "Pick one role-specific skill to improve this week and schedule 3 focused sessions.",
            "Build a small project that demonstrates the skill and publish it.",
            "Update your resume/LinkedIn with the project and measurable outcomes.",
        ],
        "resources": [
            {"title": "LinkedIn Jobs", "url": "https://www.linkedin.com/jobs/"},
            {"title": "GitHub", "url": "https://github.com/"},
        ],
        "interview_prep": [
            "Prepare 3 strong stories using the STAR format (Situation, Task, Action, Result).",
            "Practice explaining your projects in 2 minutes and 10 minutes.",
        ],
        "how_to_apply": [
            "Tailor your resume to each role and apply consistently (quality + volume).",
            "Ask for referrals and feedback; iterate every week.",
        ],
    }


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [str(value)]


def _normalize_resources(resources):
    resources = _ensure_list(resources)
    normalized = []
    for r in resources:
        if isinstance(r, dict):
            title = (r.get("title") or r.get("name") or "Resource").strip() or "Resource"
            url = (r.get("url") or "").strip()
            normalized.append({"title": title, "url": url})
        else:
            normalized.append({"title": str(r), "url": ""})
    return normalized


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
    """Uses GenAI when configured; falls back to a local heuristic otherwise."""

    skills = (data.get("skills", "") or "").lower()
    interests = (data.get("interests", "") or "").lower()
    strengths = (data.get("strengths", "") or "").lower()
    long_term_goal = (data.get("long_term_goal", "") or "").lower()
    preferred_work_style = (data.get("preferred_work_style", "") or "").lower()

    # Tokenize responses to reduce accidental matches (e.g., "candidate" vs "data")
    tokens = set(
        re.findall(
            r"[a-zA-Z]+",
            " ".join([skills, interests, strengths, long_term_goal, preferred_work_style]),
        )
    )

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
                "generation_source": "heuristic",
                "model_name": "local",
                "prompt_version": PROMPT_VERSION,
                **_default_action_plan_for("Data Scientist"),
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
                "generation_source": "heuristic",
                "model_name": "local",
                "prompt_version": PROMPT_VERSION,
                **_default_action_plan_for("Machine Learning Engineer"),
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
                "generation_source": "heuristic",
                "model_name": "local",
                "prompt_version": PROMPT_VERSION,
                **_default_action_plan_for("AI Product Manager"),
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
                "generation_source": "heuristic",
                "model_name": "local",
                "prompt_version": PROMPT_VERSION,
                **_default_action_plan_for("MLOps Engineer"),
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
                "generation_source": "heuristic",
                "model_name": "local",
                "prompt_version": PROMPT_VERSION,
                **_default_action_plan_for("AI Solutions / Sales Engineer"),
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
                "generation_source": "heuristic",
                "model_name": "local",
                "prompt_version": PROMPT_VERSION,
                **_default_action_plan_for("Business Analyst"),
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
                "generation_source": "heuristic",
                "model_name": "local",
                "prompt_version": PROMPT_VERSION,
                **_default_action_plan_for("Project Coordinator"),
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
                "generation_source": "heuristic",
                "model_name": "local",
                "prompt_version": PROMPT_VERSION,
                **_default_action_plan_for("AI UX Designer"),
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
                "generation_source": "heuristic",
                "model_name": "local",
                "prompt_version": PROMPT_VERSION,
                **_default_action_plan_for("Technical Writer"),
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
                    "generation_source": "heuristic",
                    "model_name": "local",
                    "prompt_version": PROMPT_VERSION,
                    **_default_action_plan_for("AI Product Specialist"),
                },
                {
                    "career": "Technical Writer (AI)",
                    "score": 7,
                    "reason": "Communication focus assumed.",
                    "benefits": "Explain complex ideas; flexible/remote friendly.",
                    "opportunities": "Docs teams, DevRel content, education.",
                    "sub_careers": ["Docs Specialist", "Content Strategist"],
                    "generation_source": "heuristic",
                    "model_name": "local",
                    "prompt_version": PROMPT_VERSION,
                    **_default_action_plan_for("Technical Writer"),
                },
                {
                    "career": "AI Project Coordinator",
                    "score": 7,
                    "reason": "Coordination and delivery focus assumed.",
                    "benefits": "Plan and ship; cross-team collaboration.",
                    "opportunities": "Implementation projects, PMO roles.",
                    "sub_careers": ["Program Coordinator", "Implementation Lead"],
                    "generation_source": "heuristic",
                    "model_name": "local",
                    "prompt_version": PROMPT_VERSION,
                    **_default_action_plan_for("Project Coordinator"),
                },
                {
                    "career": "Business Analyst",
                    "score": 7,
                    "reason": "Business/operations focus assumed.",
                    "benefits": "Improve processes and decisions; stakeholder-facing.",
                    "opportunities": "Operations, strategy, transformation teams.",
                    "sub_careers": ["Operations Analyst", "Strategy Analyst"],
                    "generation_source": "heuristic",
                    "model_name": "local",
                    "prompt_version": PROMPT_VERSION,
                    **_default_action_plan_for("Business Analyst"),
                },
            ]
        )

    prompt = (
        "Given this user's background, suggest 3 careers as strict JSON with the shape "
        '{"recommendations":[{"career":"...","score":int,"reason":"...","benefits":"...","opportunities":"...",'
        '"sub_careers":["..."],'
        '"getting_started":["..."],'
        '"resources":[{"title":"...","url":"..."}],'
        '"interview_prep":["..."],'
        '"how_to_apply":["..."]}]}. '
        "No markdown, no extra text, only valid JSON. Keep scores 6-10. "
        f"Skills: {skills}. Interests: {interests}. Strengths: {strengths}. "
        f"Work style: {preferred_work_style}. Long-term goal: {long_term_goal}."
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

                normalized_recs = []
                for r in recs:
                    career_name = r.get("career") or "Career"
                    defaults = _default_action_plan_for(career_name)

                    normalized_recs.append(
                        {
                            "career": career_name,
                            "score": r.get("score", 7),
                            "reason": r.get("reason", ""),
                            "benefits": r.get("benefits", ""),
                            "opportunities": r.get("opportunities", ""),
                            "sub_careers": _ensure_list(r.get("sub_careers") or r.get("sub_roles")),
                            "getting_started": _ensure_list(r.get("getting_started") or defaults.get("getting_started")),
                            "resources": _normalize_resources(r.get("resources") or defaults.get("resources")),
                            "interview_prep": _ensure_list(r.get("interview_prep") or defaults.get("interview_prep")),
                            "how_to_apply": _ensure_list(r.get("how_to_apply") or defaults.get("how_to_apply")),
                            "generation_source": "genai",
                            "model_name": GENAI_MODEL,
                            "prompt_version": PROMPT_VERSION,
                        }
                    )

                if normalized_recs:
                    return {"recommendations": normalized_recs[:3]}
        except Exception:
            # Fallback to heuristic if parsing fails
            pass

    # Ensure base recommendations always contain metadata, even if new roles were added without it.
    normalized_base = []
    for r in base[:3]:
        normalized_base.append(
            {
                **r,
                "generation_source": r.get("generation_source") or "heuristic",
                "model_name": r.get("model_name") or "local",
                "prompt_version": r.get("prompt_version") or PROMPT_VERSION,
            }
        )

    return {"recommendations": normalized_base}
