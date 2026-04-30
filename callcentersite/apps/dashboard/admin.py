from django.contrib import admin
from apps.dashboard.models import DashboardConfig, SavedFilter

admin.site.register(DashboardConfig)
admin.site.register(SavedFilter)
