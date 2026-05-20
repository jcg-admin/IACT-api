"""
apps/users/viewsets/profile_viewset.py

UC_USR_07 — Editar Perfil Propio (redireccion a endpoint canonico).

Redirección a los endpoints canónicos de perfil.

ProfileView y SettingsView implementados en apps/users/profile_view.py.
UserProfile y UserSettings fueron eliminados en FASE 4.

Los endpoints canónicos son:
  GET/PATCH /api/users/profile/   → apps.users.profile_view.ProfileView
  GET/PATCH /api/users/settings/  → apps.users.profile_view.SettingsView
"""

# Este módulo se conserva solo para mantener la compatibilidad del
# __init__.py de viewsets. No registra ninguna URL adicional.
# Ver apps/users/urls.py para las rutas actuales.

class ProfileViewSet:
    """
    Stub de compatibilidad.
    Los endpoints de perfil se sirven en ProfileView y SettingsView.
    """
    pass
