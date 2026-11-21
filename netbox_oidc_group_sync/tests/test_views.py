"""
Tests for UI views (list, detail, edit, delete, config).

Run from the NetBox directory:
    python manage.py test netbox_oidc_group_sync.tests.test_views
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from netbox_oidc_group_sync.models import OIDCGroupSyncConfig

# TODO: Add view tests
# - List view returns 200
# - Detail view returns 200
# - Add form renders and submits
# - Edit form renders and submits
# - Delete confirmation renders and submits
# - Bulk edit / bulk delete

User = get_user_model()

CONFIG_URL = reverse('plugins:netbox_oidc_group_sync:config')
CONFIG_POST_DATA = {
    'group_claim_name': 'groups',
    'sync_mode': 'replace',
    'superuser_groups': 'attacker-group',
}


class OIDCGroupSyncConfigViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='regular')
        cls.superuser = User.objects.create_user(username='admin', is_superuser=True)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(CONFIG_URL)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_anonymous_cannot_update_config(self):
        response = self.client.post(CONFIG_URL, CONFIG_POST_DATA)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OIDCGroupSyncConfig.get_solo().superuser_groups, '')

    def test_regular_user_cannot_view_config(self):
        self.client.force_login(self.user)
        response = self.client.get(CONFIG_URL)
        self.assertEqual(response.status_code, 403)

    def test_regular_user_cannot_update_config(self):
        self.client.force_login(self.user)
        response = self.client.post(CONFIG_URL, CONFIG_POST_DATA)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(OIDCGroupSyncConfig.get_solo().superuser_groups, '')

    def test_superuser_can_view_config(self):
        self.client.force_login(self.superuser)
        response = self.client.get(CONFIG_URL)
        self.assertEqual(response.status_code, 200)

    def test_superuser_can_update_config(self):
        self.client.force_login(self.superuser)
        response = self.client.post(CONFIG_URL, CONFIG_POST_DATA)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OIDCGroupSyncConfig.get_solo().superuser_groups, 'attacker-group')
