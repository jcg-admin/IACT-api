"""
URLs para access app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModuleViewSet, UserModuleAccessViewSet, MyModulesView

# Router para ViewSets
router = DefaultRouter()
router.register(r'modules', ModuleViewSet, basename='module')
router.register(r'module-accesses', UserModuleAccessViewSet, basename='moduleaccess')

app_name = 'access'

urlpatterns = [
    # ViewSets (router)
    path('', include(router.urls)),
    
    # Endpoints personalizados
    path('my-modules/', MyModulesView.as_view(), name='my-modules'),
]
