from django.contrib import admin
from apps.alerts.models import InternalMessage, AlertConfiguration, AlertSubscription

admin.site.register(InternalMessage)
admin.site.register(AlertConfiguration)
admin.site.register(AlertSubscription)
