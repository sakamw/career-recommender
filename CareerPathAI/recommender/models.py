from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


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

    # "Action plan" fields to help the user actually get started.
    # Stored as JSON to keep them flexible and easy to render as lists.
    getting_started = models.JSONField(default=list, blank=True)
    resources = models.JSONField(default=list, blank=True)
    interview_prep = models.JSONField(default=list, blank=True)
    how_to_apply = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.career_name} ({self.score}/10)"

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        """Move to recycle bin"""
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore from recycle bin"""
        self.deleted_at = None
        self.save()

    @classmethod
    def cleanup_old_deleted(cls, days=30):
        """Permanently delete items in recycle bin"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(deleted_at__lt=cutoff_date).delete()
