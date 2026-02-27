import django_filters
from users.models import Group
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet

from .models import OIDCGroupMapping


class OIDCGroupMappingFilterSet(NetBoxModelFilterSet):
    oidc_group_name = django_filters.CharFilter(lookup_expr='icontains')
    group_id = django_filters.ModelChoiceFilter(
        queryset=Group.objects.all(),
        field_name='group',
        label='NetBox Group',
    )

    class Meta:
        model = OIDCGroupMapping
        fields = ('id', 'oidc_group_name', 'group_id')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(oidc_group_name__icontains=value) |
            Q(group__name__icontains=value) |
            Q(description__icontains=value)
        )
