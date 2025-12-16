from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .ai import generate_career_recommendation
from .forms import QuestionnaireForm, UserProfileForm
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


def _clear_messages(request):
    list(messages.get_messages(request))


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "recommender/landing.html")


def _prep_user_form(form: UserCreationForm) -> UserCreationForm:
    for name, field in form.fields.items():
        field.widget.attrs.setdefault("class", "form-control")
        field.widget.attrs.setdefault("required", True)
        if "password" in name:
            field.widget.attrs.setdefault("type", "password")
    return form


def register(request):
    form = _prep_user_form(UserCreationForm(request.POST or None))
    if request.method != "POST":
        _clear_messages(request)
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
    form = _prep_user_form(UserCreationForm())
    if request.method != "POST":
        _clear_messages(request)
    return render(request, "recommender/auth_register.html", {"form": form, "login_mode": True})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    # Get active recommendations (not deleted)
    recs = Recommendation.objects.filter(
        questionnaire__user=request.user,
        deleted_at__isnull=True
    ).order_by("-created_at")[:5]
    
    # Get recycle bin items (deleted within last 30 days)
    cutoff_date = timezone.now() - timedelta(days=30)
    recycle_bin = Recommendation.objects.filter(
        questionnaire__user=request.user,
        deleted_at__isnull=False,
        deleted_at__gte=cutoff_date
    ).order_by("-deleted_at")
    
    # Auto-cleanup old deleted items (older than 30 days)
    Recommendation.cleanup_old_deleted(days=30)
    
    return render(request, "recommender/dashboard.html", {
        "recommendations": recs,
        "recycle_bin": recycle_bin
    })


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    form = UserProfileForm(request.POST or None, instance=profile_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("profile")
    return render(request, "recommender/profile.html", {"form": form})


@login_required
def questionnaire(request):
    form = QuestionnaireForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        questionnaire = form.save(commit=False)
        questionnaire.user = request.user
        questionnaire.save()

        ai_result = generate_career_recommendation(form.cleaned_data)
        recs = ai_result.get("recommendations", [])[:1]  # limit to a single feedback per questionnaire
        for item in recs:
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
                getting_started=item.get("getting_started") or [],
                resources=item.get("resources") or [],
                interview_prep=item.get("interview_prep") or [],
                how_to_apply=item.get("how_to_apply") or [],
            )
        return redirect("dashboard")
    return render(request, "recommender/questionnaire.html", {"form": form})


@login_required
def recommendation_detail(request, pk):
    rec = get_object_or_404(Recommendation, pk=pk, questionnaire__user=request.user)
    if rec.deleted_at is not None:
        messages.warning(request, "This recommendation is in the recycle bin.")
        return redirect("dashboard")
    parsed = _parse_explanation(rec.explanation)
    return render(
        request,
        "recommender/recommendation_detail.html",
        {
            "rec": rec,
            "details": parsed,  # legacy (older recs)
        },
    )


@login_required
def delete_recommendation(request, pk):
    """Move recommendation to recycle bin"""
    rec = get_object_or_404(Recommendation, pk=pk, questionnaire__user=request.user)
    if rec.deleted_at is None:
        rec.soft_delete()
        messages.success(request, f"'{rec.career_name}' moved to recycle bin.")
    return redirect("dashboard")


@login_required
def restore_recommendation(request, pk):
    """Restore recommendation from recycle bin"""
    rec = get_object_or_404(Recommendation, pk=pk, questionnaire__user=request.user)
    if rec.deleted_at is not None:
        rec.restore()
        messages.success(request, f"'{rec.career_name}' restored from recycle bin.")
    return redirect("dashboard")
