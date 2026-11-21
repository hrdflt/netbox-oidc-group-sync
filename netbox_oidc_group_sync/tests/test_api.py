"""
Tests for the REST API endpoints.

Run from the NetBox directory:
    python manage.py test netbox_oidc_group_sync.tests.test_api
"""
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from netbox_oidc_group_sync.models import OIDCGroupSyncConfig

# TODO: Add API tests
# - GET /api/plugins/oidc-group-sync/mappings/ returns 200
# - POST creates a mapping
# - GET /api/plugins/oidc-group-sync/mappings/{id}/ returns mapping
# - PUT/PATCH updates a mapping
# - DELETE removes a mapping

User = get_user_model()

CONFIG_URL = reverse('plugins-api:netbox_oidc_group_sync-api:config')


class OIDCGroupSyncConfigAPITest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='regular')
        cls.superuser = User.objects.create_user(username='admin', is_superuser=True)

    def setUp(self):
        self.client = APIClient()

    def test_anonymous_cannot_access_config(self):
        response = self.client.get(CONFIG_URL)
        self.assertIn(response.status_code, (401, 403))

    def test_regular_user_cannot_view_config(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CONFIG_URL)
        self.assertEqual(response.status_code, 403)

    def test_regular_user_cannot_update_config(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(CONFIG_URL, {'superuser_groups': 'attacker-group'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(OIDCGroupSyncConfig.get_solo().superuser_groups, '')

    def test_regular_user_cannot_replace_config(self):
        self.client.force_authenticate(user=self.user)
        data = {'group_claim_name': 'groups', 'sync_mode': 'replace', 'superuser_groups': 'attacker-group'}
        response = self.client.put(CONFIG_URL, data, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(OIDCGroupSyncConfig.get_solo().superuser_groups, '')

    def test_superuser_read_only_token_cannot_update_config(self):
        token = SimpleNamespace(write_enabled=False)
        self.client.force_authenticate(user=self.superuser, token=token)
        response = self.client.patch(CONFIG_URL, {'superuser_groups': 'attacker-group'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(OIDCGroupSyncConfig.get_solo().superuser_groups, '')

    def test_superuser_read_only_token_can_view_config(self):
        token = SimpleNamespace(write_enabled=False)
        self.client.force_authenticate(user=self.superuser, token=token)
        response = self.client.get(CONFIG_URL)
        self.assertEqual(response.status_code, 200)

    def test_superuser_token_without_write_flag_cannot_update_config(self):
        self.client.force_authenticate(user=self.superuser, token=SimpleNamespace())
        response = self.client.patch(CONFIG_URL, {'superuser_groups': 'attacker-group'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(OIDCGroupSyncConfig.get_solo().superuser_groups, '')

    def test_superuser_write_enabled_token_can_update_config(self):
        token = SimpleNamespace(write_enabled=True)
        self.client.force_authenticate(user=self.superuser, token=token)
        response = self.client.patch(CONFIG_URL, {'superuser_groups': 'netbox-admins'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OIDCGroupSyncConfig.get_solo().superuser_groups, 'netbox-admins')

    def test_superuser_can_update_config(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.patch(CONFIG_URL, {'superuser_groups': 'netbox-admins'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OIDCGroupSyncConfig.get_solo().superuser_groups, 'netbox-admins')
