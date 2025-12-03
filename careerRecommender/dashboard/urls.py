from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('sign-in/', views.dashboard_sign_in, name='dashboard_sign_in'),
    path('sign-up/', views.dashboard_sign_up, name='dashboard_sign_up'),
    path('profile/', views.dashboard_profile, name='dashboard_profile'),
    path('logout/', views.dashboard_logout, name='dashboard_logout'),
]
