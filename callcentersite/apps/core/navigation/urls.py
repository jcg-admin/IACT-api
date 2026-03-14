"""
Navigation URLs
"""

from django.urls import path
from .views import user_menu_view

app_name = 'navigation'

urlpatterns = [
    path('menu/', user_menu_view, name='user-menu'),
]
