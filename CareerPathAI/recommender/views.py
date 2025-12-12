from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render

from .ai import generate_career_recommendation
from .forms import QuestionnaireForm
from .models import Questionnaire, Recommendation, UserProfile


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
            Recommendation.objects.create(
                questionnaire=questionnaire,
                career_name=item.get("career", "Career"),
                score=item.get("score", 7),
                explanation=item.get("reason", "N/A"),
            )
        return redirect("dashboard")
    return render(request, "recommender/questionnaire.html", {"form": form})


@login_required
def recommendation_detail(request, pk):
    rec = get_object_or_404(Recommendation, pk=pk, questionnaire__user=request.user)
    return render(request, "recommender/recommendation_detail.html", {"rec": rec})
