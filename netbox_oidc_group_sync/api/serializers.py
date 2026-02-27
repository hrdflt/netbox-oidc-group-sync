from users.models import Group
from rest_framework import serializers
from netbox.api.serializers import NetBoxModelSerializer

from ..models import OIDCGroupMapping, OIDCGroupSyncConfig


class NestedGroupSerializer(serializers.ModelSerializer):
    """Minimal serializer for Django auth.Group."""
    class Meta:
        model = Group
        fields = ('id', 'name')


class OIDCGroupMappingSerializer(NetBoxModelSerializer):
    group = NestedGroupSerializer(read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        source='group',
        write_only=True,
    )

    class Meta:
        model = OIDCGroupMapping
        fields = (
            'id', 'url', 'display',
            'oidc_group_name', 'group', 'group_id', 'description',
            'tags', 'created', 'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'oidc_group_name', 'group')


class OIDCGroupSyncConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = OIDCGroupSyncConfig
        fields = (
            'id', 'group_claim_name', 'auto_create_groups',
            'sync_mode', 'superuser_groups',
            'created', 'last_updated',
        )
        read_only_fields = ('id', 'created', 'last_updated')
