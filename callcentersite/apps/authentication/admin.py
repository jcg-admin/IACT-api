from django.contrib import admin
from apps.authentication.models import SecurityQuestion, UserSecurityAnswer, LoginAttempt, SessionLog

admin.site.register(SecurityQuestion)
admin.site.register(UserSecurityAnswer)
admin.site.register(LoginAttempt)
admin.site.register(SessionLog)
