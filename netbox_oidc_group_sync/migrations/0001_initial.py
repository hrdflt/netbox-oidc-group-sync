import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0006_custom_group_model'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='OIDCGroupMapping',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'custom_field_data',
                    models.JSONField(blank=True, default=dict, encoder=None),
                ),
                (
                    'oidc_group_name',
                    models.CharField(
                        help_text=(
                            'Group name or ID as it appears in the OIDC token claims'
                        ),
                        max_length=256,
                        unique=True,
                    ),
                ),
                (
                    'description',
                    models.CharField(blank=True, max_length=500),
                ),
                (
                    'group',
                    models.ForeignKey(
                        help_text=(
                            'Django group to assign when the OIDC group is present'
                        ),
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='oidc_mappings',
                        to='users.group',
                    ),
                ),
                (
                    'tags',
                    models.ManyToManyField(blank=True, to='extras.tag'),
                ),
            ],
            options={
                'ordering': ['oidc_group_name'],
            },
        ),
        migrations.CreateModel(
            name='OIDCGroupSyncConfig',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'group_claim_name',
                    models.CharField(
                        default='groups',
                        help_text='OIDC token claim containing group names',
                        max_length=128,
                    ),
                ),
                (
                    'auto_create_groups',
                    models.BooleanField(
                        default=False,
                        help_text=(
                            'Automatically create Django groups for unmapped OIDC groups'
                        ),
                    ),
                ),
                (
                    'sync_mode',
                    models.CharField(
                        choices=[
                            ('replace', 'Replace'),
                            ('additive', 'Additive'),
                        ],
                        default='replace',
                        help_text=(
                            "'Replace' removes groups not in the OIDC claim; "
                            "'Additive' only adds."
                        ),
                        max_length=16,
                    ),
                ),
                (
                    'superuser_groups',
                    models.TextField(
                        blank=True,
                        default='',
                        help_text=(
                            'Comma-separated list of OIDC group names that grant '
                            'superuser status'
                        ),
                    ),
                ),
            ],
            options={
                'verbose_name': 'OIDC Group Sync Configuration',
            },
        ),
    ]
