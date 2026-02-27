from django import forms
from netbox.forms import NetBoxModelForm, NetBoxModelBulkEditForm, NetBoxModelImportForm, NetBoxModelFilterSetForm
from users.models import Group
from utilities.forms.fields import CSVModelChoiceField, DynamicModelChoiceField, TagFilterField

from .models import OIDCGroupMapping, OIDCGroupSyncConfig


class OIDCGroupMappingForm(NetBoxModelForm):
    group = DynamicModelChoiceField(
        queryset=Group.objects.all(),
        label='NetBox Group',
    )

    class Meta:
        model = OIDCGroupMapping
        fields = ('oidc_group_name', 'group', 'description', 'tags')


class OIDCGroupMappingBulkEditForm(NetBoxModelBulkEditForm):
    model = OIDCGroupMapping
    group = DynamicModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='NetBox Group',
    )
    description = forms.CharField(
        max_length=500,
        required=False,
    )

    fieldsets = (
        (None, ('group', 'description')),
    )
    nullable_fields = ('description',)


class OIDCGroupMappingImportForm(NetBoxModelImportForm):
    group = CSVModelChoiceField(
        queryset=Group.objects.all(),
        to_field_name='name',
        help_text='Django group name',
    )

    class Meta:
        model = OIDCGroupMapping
        fields = ('oidc_group_name', 'group', 'description')


class OIDCGroupMappingFilterForm(NetBoxModelFilterSetForm):
    model = OIDCGroupMapping
    oidc_group_name = forms.CharField(required=False)
    group_id = DynamicModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='NetBox Group',
    )
    tag = TagFilterField(model)


class OIDCGroupSyncConfigForm(forms.ModelForm):
    class Meta:
        model = OIDCGroupSyncConfig
        fields = ('group_claim_name', 'auto_create_groups', 'sync_mode', 'superuser_groups')
        widgets = {
            'group_claim_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sync_mode': forms.Select(attrs={'class': 'form-select'}),
            'superuser_groups': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Comma-separated OIDC group names',
            }),
        }
