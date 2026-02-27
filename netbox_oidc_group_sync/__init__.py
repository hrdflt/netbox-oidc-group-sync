from netbox.plugins import PluginConfig


class NetBoxOIDCGroupSyncConfig(PluginConfig):
    name = 'netbox_oidc_group_sync'
    verbose_name = 'OIDC Group Sync'
    description = 'Sync OIDC provider groups to NetBox/Django groups'
    version = '0.1.0'
    author = 'Hardfault'
    author_email = ''
    base_url = 'oidc-group-sync'
    min_version = '4.0.0'
    project_url = 'https://github.com/hrdflt/netbox-oidc-group-sync'
    default_settings = {
        'group_claim_name': 'groups',
        'auto_create_groups': False,
        'sync_mode': 'replace',
    }


config = NetBoxOIDCGroupSyncConfig
