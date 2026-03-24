"""URL patterns for the navigation system."""
from django.urls import path

from apps.core.navigation import views

app_name = 'navigation'

urlpatterns = [
    path('', views.get_navigation_view, name='navigation'),
]
