"""
URLs para el sistema de navegacion.
"""
from django.urls import path

from . import views

app_name = 'navigation'

urlpatterns = [
    path('menu/', views.navigation_menu_view, name='menu'),
    path('modules/', views.navigation_modules_view, name='modules'),
]
