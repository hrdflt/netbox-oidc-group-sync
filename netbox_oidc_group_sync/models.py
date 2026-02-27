from django.db import models
from users.models import Group

from netbox.models import NetBoxModel


class OIDCGroupMapping(NetBoxModel):
    """Maps an OIDC provider group name to a Django/NetBox group."""

    oidc_group_name = models.CharField(
        max_length=256,
        unique=True,
        help_text="Group name or ID as it appears in the OIDC token claims",
    )
    group = models.ForeignKey(
        to=Group,
        on_delete=models.CASCADE,
        related_name='oidc_mappings',
        help_text="Django group to assign when the OIDC group is present",
    )
    description = models.CharField(
        max_length=500,
        blank=True,
    )

    class Meta:
        ordering = ['oidc_group_name']
        verbose_name = 'OIDC Group Mapping'
        verbose_name_plural = 'OIDC Group Mappings'

    def __str__(self):
        return f"{self.oidc_group_name} → {self.group.name}"

    def clone(self):
        return {
            'oidc_group_name': self.oidc_group_name,
            'group': self.group,
            'description': self.description,
        }


class OIDCGroupSyncConfig(models.Model):
    """Singleton configuration for OIDC group sync behaviour."""

    created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)

    group_claim_name = models.CharField(
        max_length=128,
        default='groups',
        help_text="OIDC token claim containing group names",
    )
    auto_create_groups = models.BooleanField(
        default=False,
        help_text="Automatically create Django groups for unmapped OIDC groups",
    )
    sync_mode = models.CharField(
        max_length=16,
        choices=[
            ('replace', 'Replace'),
            ('additive', 'Additive'),
        ],
        default='replace',
        help_text="'Replace' removes groups not in the OIDC claim; 'Additive' only adds.",
    )
    superuser_groups = models.TextField(
        blank=True,
        default='',
        help_text="Comma-separated list of OIDC group names that grant superuser status",
    )

    class Meta:
        verbose_name = "OIDC Group Sync Configuration"

    def __str__(self):
        return "OIDC Group Sync Configuration"

    # ------------------------------------------------------------------
    # Singleton enforcement
    # ------------------------------------------------------------------

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Prevent deletion of the singleton

    @classmethod
    def get_solo(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def get_superuser_groups_list(self):
        """Return superuser_groups as a list of stripped, non-empty strings."""
        return [g.strip() for g in self.superuser_groups.split(',') if g.strip()]
