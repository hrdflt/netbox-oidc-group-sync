"""
Tests for the social-auth pipeline function sync_oidc_groups.

Run from the NetBox directory:
    python manage.py test netbox_oidc_group_sync.tests.test_pipeline
"""
# TODO: Add pipeline tests (mock social-auth backend)
# - Groups synced in replace mode
# - Groups synced in additive mode
# - Auto-create groups when enabled
# - No groups claim → no changes
# - String claim (single group) handled
# - Superuser flag set/unset based on OIDC groups
# - Empty superuser config → flags untouched
