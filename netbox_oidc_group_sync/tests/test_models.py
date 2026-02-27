"""
Tests for OIDCGroupMapping and OIDCGroupSyncConfig models.

Run from the NetBox directory:
    python manage.py test netbox_oidc_group_sync.tests.test_models
"""
# TODO: Add model tests
# - OIDCGroupMapping CRUD
# - OIDCGroupMapping.clone()
# - OIDCGroupMapping.__str__() format
# - OIDCGroupSyncConfig singleton enforcement (pk always 1)
# - OIDCGroupSyncConfig.get_solo() creates on first call
# - OIDCGroupSyncConfig.delete() is a no-op
# - OIDCGroupSyncConfig.get_superuser_groups_list() parsing
