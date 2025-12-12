from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    headline = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.user.username


class Questionnaire(models.Model):
    WORK_STYLE_CHOICES = [
        ("Solo", "Solo"),
        ("Team", "Team"),
        ("Mixed", "Mixed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questionnaires")
    skills = models.TextField()
    interests = models.TextField()
    strengths = models.TextField()
    preferred_work_style = models.CharField(max_length=10, choices=WORK_STYLE_CHOICES)
    long_term_goal = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Questionnaire {self.id} by {self.user.username}"


class Recommendation(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name="recommendations")
    career_name = models.CharField(max_length=150)
    score = models.PositiveIntegerField()
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.career_name} ({self.score}/10)"
