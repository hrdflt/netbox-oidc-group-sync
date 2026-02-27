from netbox.plugins import PluginMenuButton, PluginMenuItem

menu_items = (
    PluginMenuItem(
        link='plugins:netbox_oidc_group_sync:oidcgroupmapping_list',
        link_text='Group Mappings',
        buttons=(
            PluginMenuButton(
                link='plugins:netbox_oidc_group_sync:oidcgroupmapping_add',
                title='Add',
                icon_class='mdi mdi-plus-thick',
            ),
        ),
    ),
    PluginMenuItem(
        link='plugins:netbox_oidc_group_sync:config',
        link_text='Configuration',
    ),
)
