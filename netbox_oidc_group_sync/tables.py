import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import OIDCGroupMapping


class OIDCGroupMappingTable(NetBoxTable):
    oidc_group_name = tables.Column(linkify=True)
    group = tables.Column(accessor='group__name', verbose_name='NetBox Group')
    description = tables.Column()
    tags = columns.TagColumn(url_name='plugins:netbox_oidc_group_sync:oidcgroupmapping_list')
    actions = columns.ActionsColumn()

    class Meta(NetBoxTable.Meta):
        model = OIDCGroupMapping
        fields = ('pk', 'id', 'oidc_group_name', 'group', 'description', 'tags', 'actions')
        default_columns = ('oidc_group_name', 'group', 'description', 'tags')
