from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import SAFE_METHODS, BasePermission
from netbox.api.viewsets import NetBoxModelViewSet

from ..models import OIDCGroupMapping, OIDCGroupSyncConfig
from ..filtersets import OIDCGroupMappingFilterSet
from .serializers import OIDCGroupMappingSerializer, OIDCGroupSyncConfigSerializer


class IsSuperuser(BasePermission):
    """
    Allow access to superusers only. Unsafe methods also require the API
    token (if any) to be write-enabled, matching NetBox's TokenPermissions.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.is_superuser):
            return False
        if request.method in SAFE_METHODS or request.auth is None:
            return True
        return bool(getattr(request.auth, 'write_enabled', False))


class OIDCGroupMappingViewSet(NetBoxModelViewSet):
    queryset = OIDCGroupMapping.objects.all()
    serializer_class = OIDCGroupMappingSerializer
    filterset_class = OIDCGroupMappingFilterSet


class OIDCGroupSyncConfigView(APIView):
    """
    Singleton config endpoint.
    GET returns the current config; PUT/PATCH updates it.

    Superuser only -- see OIDCGroupSyncConfigView in views.py.
    """
    permission_classes = [IsSuperuser]

    def get(self, request):
        config = OIDCGroupSyncConfig.get_solo()
        serializer = OIDCGroupSyncConfigSerializer(config)
        return Response(serializer.data)

    def put(self, request):
        config = OIDCGroupSyncConfig.get_solo()
        serializer = OIDCGroupSyncConfigSerializer(config, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        config = OIDCGroupSyncConfig.get_solo()
        serializer = OIDCGroupSyncConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
