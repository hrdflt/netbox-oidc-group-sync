from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from netbox.api.viewsets import NetBoxModelViewSet

from ..models import OIDCGroupMapping, OIDCGroupSyncConfig
from ..filtersets import OIDCGroupMappingFilterSet
from .serializers import OIDCGroupMappingSerializer, OIDCGroupSyncConfigSerializer


class OIDCGroupMappingViewSet(NetBoxModelViewSet):
    queryset = OIDCGroupMapping.objects.all()
    serializer_class = OIDCGroupMappingSerializer
    filterset_class = OIDCGroupMappingFilterSet


class OIDCGroupSyncConfigView(APIView):
    """
    Singleton config endpoint.
    GET returns the current config; PUT/PATCH updates it.
    """
    permission_classes = [IsAuthenticated]

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
