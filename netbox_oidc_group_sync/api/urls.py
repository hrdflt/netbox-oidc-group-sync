from netbox.api.routers import NetBoxRouter
from django.urls import path
from . import views

router = NetBoxRouter()
router.register('mappings', views.OIDCGroupMappingViewSet)

urlpatterns = [
    path('config/', views.OIDCGroupSyncConfigView.as_view(), name='config'),
] + router.urls
