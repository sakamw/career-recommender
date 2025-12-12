from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("questionnaire/", views.questionnaire, name="questionnaire"),
    path("recommendation/<int:pk>/", views.recommendation_detail, name="recommendation_detail"),
    path("recommendation/<int:pk>/delete/", views.delete_recommendation, name="delete_recommendation"),
    path("recommendation/<int:pk>/restore/", views.restore_recommendation, name="restore_recommendation"),
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
]

