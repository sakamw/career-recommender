from django.contrib import admin

from .models import Questionnaire, Recommendation, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline")


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ("user", "preferred_work_style", "created_at")
    search_fields = ("user__username", "skills", "interests")


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("career_name", "score", "created_at")
    list_filter = ("score",)
