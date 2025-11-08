"""
URL routes for authentication endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('check-username/', views.check_username_availability, name='check-username'),
    path('search-players/', views.search_players, name='search-players'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/<int:pk>/', views.UserProfileView.as_view(), name='profile-by-id'),
]

