from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render

from .ai import generate_career_recommendation
from .forms import QuestionnaireForm
from .models import Questionnaire, Recommendation, UserProfile


def _parse_explanation(text: str) -> dict:
    """
    Expected format:
    Why: ...
    Benefits: ...
    Employment opportunities: ...
    Related sub-paths: ...
    """
    parsed = {"why": "", "benefits": "", "opportunities": "", "sub_paths": []}
    if not text:
        return parsed

    for line in text.splitlines():
        lower = line.lower()
        if line.startswith("Why:"):
            parsed["why"] = line.replace("Why:", "", 1).strip()
        elif lower.startswith("benefits:"):
            parsed["benefits"] = line.split(":", 1)[1].strip() if ":" in line else line.strip()
        elif lower.startswith("employment opportunities:"):
            parsed["opportunities"] = line.split(":", 1)[1].strip() if ":" in line else line.strip()
        elif lower.startswith("related sub-paths:"):
            sub = line.split(":", 1)[1].strip() if ":" in line else ""
            parsed["sub_paths"] = [s.strip() for s in sub.split(",") if s.strip()]
    return parsed


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "recommender/landing.html")


def register(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        UserProfile.objects.create(user=user)
        login(request, user)
        messages.success(request, "Account created.")
        return redirect("dashboard")
    return render(request, "recommender/auth_register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid credentials.")
    return render(request, "recommender/auth_register.html", {"form": UserCreationForm(), "login_mode": True})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    recs = Recommendation.objects.filter(questionnaire__user=request.user).order_by("-created_at")[:5]
    return render(request, "recommender/dashboard.html", {"recommendations": recs})


@login_required
def questionnaire(request):
    form = QuestionnaireForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        questionnaire = form.save(commit=False)
        questionnaire.user = request.user
        questionnaire.save()

        ai_result = generate_career_recommendation(form.cleaned_data)
        for item in ai_result.get("recommendations", []):
            reason = item.get("reason", "Why not provided.")
            benefits = item.get("benefits", "Benefits not provided.")
            opportunities = item.get("opportunities", "Opportunities not provided.")
            subs = item.get("sub_careers") or item.get("sub_roles") or []
            if isinstance(subs, (list, tuple)):
                sub_text = ", ".join(subs)
            else:
                sub_text = str(subs)
            explanation_text = (
                f"Why: {reason}\n"
                f"Benefits: {benefits}\n"
                f"Employment opportunities: {opportunities}\n"
                f"Related sub-paths: {sub_text}"
            )
            Recommendation.objects.create(
                questionnaire=questionnaire,
                career_name=item.get("career", "Career"),
                score=item.get("score", 7),
                explanation=explanation_text,
            )
        return redirect("dashboard")
    return render(request, "recommender/questionnaire.html", {"form": form})


@login_required
def recommendation_detail(request, pk):
    rec = get_object_or_404(Recommendation, pk=pk, questionnaire__user=request.user)
    parsed = _parse_explanation(rec.explanation)
    return render(
        request,
        "recommender/recommendation_detail.html",
        {"rec": rec, "details": parsed},
    )
