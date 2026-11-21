"""
Tests for the social-auth pipeline function sync_oidc_groups.

Run from the NetBox directory:
    python manage.py test netbox_oidc_group_sync.tests.test_pipeline
"""
# TODO: Add auto-create tests
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase
from users.models import Group

from netbox_oidc_group_sync.models import OIDCGroupMapping, OIDCGroupSyncConfig
from netbox_oidc_group_sync.pipeline import sync_oidc_groups

User = get_user_model()


class MissingClaimTestCase(TestCase):
    """A missing or empty groups claim means the user is in no groups."""

    def setUp(self):
        self.user = User.objects.create_user(username='bob', is_superuser=True)
        self.netops = Group.objects.create(name='netops')
        self.user.groups.add(self.netops)
        OIDCGroupMapping.objects.create(oidc_group_name='idp-netops', group=self.netops)
        self.config = OIDCGroupSyncConfig.get_solo()
        self.config.sync_mode = 'replace'
        self.config.superuser_groups = 'idp-admins'
        self.config.save()

    def login(self, response, **kwargs):
        sync_oidc_groups(backend=None, user=self.user, response=response, **kwargs)
        self.user.refresh_from_db()
        return set(self.user.groups.values_list('name', flat=True))

    def test_missing_claim_removes_groups_and_superuser(self):
        groups = self.login({'email': 'bob@example.com'})

        self.assertEqual(groups, set())
        self.assertFalse(self.user.is_superuser)

    def test_empty_claim_removes_groups_and_superuser(self):
        for value in ([], '', None):
            with self.subTest(value=value):
                self.user.is_superuser = True
                self.user.save()
                self.user.groups.add(self.netops)

                groups = self.login({'groups': value})

                self.assertEqual(groups, set())
                self.assertFalse(self.user.is_superuser)

    def test_unsupported_claim_type_is_treated_as_empty(self):
        for value in ({'idp-admins': True}, 42, [7], ['idp-\x00admins'], ['idp-\ud800admins']):
            with self.subTest(value=value):
                self.user.is_superuser = True
                self.user.save()
                self.user.groups.add(self.netops)

                groups = self.login({'groups': value})

                self.assertEqual(groups, set())
                self.assertFalse(self.user.is_superuser)

    def test_non_dict_response_is_treated_as_empty(self):
        groups = self.login(None)

        self.assertEqual(groups, set())
        self.assertFalse(self.user.is_superuser)

    def test_previous_login_extra_data_is_not_used(self):
        social = SimpleNamespace(extra_data={'groups': ['idp-netops', 'idp-admins']})

        groups = self.login({}, social=social)

        self.assertEqual(groups, set())
        self.assertFalse(self.user.is_superuser)

    def test_additive_mode_keeps_groups_but_removes_superuser(self):
        self.config.sync_mode = 'additive'
        self.config.save()

        groups = self.login({})

        self.assertEqual(groups, {'netops'})
        self.assertFalse(self.user.is_superuser)

    def test_superuser_untouched_when_no_superuser_groups_configured(self):
        self.config.superuser_groups = ''
        self.config.save()

        groups = self.login({})

        self.assertEqual(groups, set())
        self.assertTrue(self.user.is_superuser)

    def test_claim_present_grants_groups_and_superuser(self):
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.clear()

        groups = self.login({'groups': ['idp-netops', 'idp-admins']})

        self.assertEqual(groups, {'netops'})
        self.assertTrue(self.user.is_superuser)

    def test_string_claim_is_a_single_group(self):
        groups = self.login({'groups': 'idp-netops'})

        self.assertEqual(groups, {'netops'})
        self.assertFalse(self.user.is_superuser)

    def test_invalid_entries_are_ignored_and_valid_ones_kept(self):
        with self.assertLogs('netbox_oidc_group_sync.pipeline', level='WARNING') as logs:
            groups = self.login({'groups': ['idp-netops', 7, '', None]})

        self.assertEqual(groups, {'netops'})
        self.assertFalse(self.user.is_superuser)
        self.assertTrue(any('Ignoring empty, non-string or invalid entries' in m for m in logs.output))


class IDTokenFallbackTestCase(TestCase):
    """The claim is taken from the validated ID token when the response lacks it."""

    def setUp(self):
        self.user = User.objects.create_user(username='carol')
        self.netops = Group.objects.create(name='netops')
        self.support = Group.objects.create(name='support')
        OIDCGroupMapping.objects.create(oidc_group_name='idp-netops', group=self.netops)
        OIDCGroupMapping.objects.create(oidc_group_name='idp-support', group=self.support)
        self.config = OIDCGroupSyncConfig.get_solo()
        self.config.sync_mode = 'replace'
        self.config.superuser_groups = 'idp-admins'
        self.config.save()

    def login(self, response, id_token):
        backend = SimpleNamespace(id_token=id_token)
        sync_oidc_groups(backend=backend, user=self.user, response=response)
        self.user.refresh_from_db()
        return set(self.user.groups.values_list('name', flat=True))

    def test_claim_only_in_id_token_is_used(self):
        groups = self.login({'email': 'carol@example.com'}, {'groups': ['idp-netops', 'idp-admins']})

        self.assertEqual(groups, {'netops'})
        self.assertTrue(self.user.is_superuser)

    def test_response_takes_precedence_over_id_token(self):
        groups = self.login({'groups': ['idp-support']}, {'groups': ['idp-netops', 'idp-admins']})

        self.assertEqual(groups, {'support'})
        self.assertFalse(self.user.is_superuser)

    def test_empty_claim_in_response_is_not_overridden(self):
        self.user.groups.add(self.netops)

        groups = self.login({'groups': []}, {'groups': ['idp-netops', 'idp-admins']})

        self.assertEqual(groups, set())
        self.assertFalse(self.user.is_superuser)

    def test_claim_in_neither_removes_access(self):
        self.user.is_superuser = True
        self.user.save()
        self.user.groups.add(self.netops)

        groups = self.login({}, {'sub': 'carol'})

        self.assertEqual(groups, set())
        self.assertFalse(self.user.is_superuser)

    def test_id_token_that_is_not_a_dict_is_ignored(self):
        for id_token in (None, 'eyJhbGciOi', ['idp-netops']):
            with self.subTest(id_token=id_token):
                self.user.is_superuser = True
                self.user.save()
                self.user.groups.add(self.netops)

                groups = self.login({}, id_token)

                self.assertEqual(groups, set())
                self.assertFalse(self.user.is_superuser)

    def test_warning_lists_response_keys_and_id_token_claims(self):
        with self.assertLogs('netbox_oidc_group_sync.pipeline', level='WARNING') as logs:
            self.login({'email': 'carol@example.com'}, {'sub': 'carol'})

        self.assertTrue(any("['email']" in m and "['sub']" in m for m in logs.output))
