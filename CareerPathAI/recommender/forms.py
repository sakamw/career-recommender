from django import forms

from .models import Questionnaire, UserProfile


class QuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ["skills", "interests", "strengths", "preferred_work_style", "long_term_goal"]
        widgets = {
            "skills": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "interests": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "strengths": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "preferred_work_style": forms.Select(attrs={"class": "form-select"}),
            "long_term_goal": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["headline", "bio"]
        widgets = {
            "headline": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


