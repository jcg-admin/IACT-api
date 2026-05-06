from django.contrib import admin
from apps.pipeline.models import ETLExecution, Center, Service, CallRecord, CallNote

admin.site.register(ETLExecution)
admin.site.register(Center)
admin.site.register(Service)
admin.site.register(CallRecord)
admin.site.register(CallNote)
