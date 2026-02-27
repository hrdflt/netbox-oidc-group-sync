from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from netbox.views import generic

from .models import OIDCGroupMapping, OIDCGroupSyncConfig
from .forms import (
    OIDCGroupMappingForm,
    OIDCGroupMappingBulkEditForm,
    OIDCGroupMappingImportForm,
    OIDCGroupMappingFilterForm,
    OIDCGroupSyncConfigForm,
)
from .tables import OIDCGroupMappingTable
from .filtersets import OIDCGroupMappingFilterSet


# --- OIDCGroupMapping CRUD views ---

class OIDCGroupMappingListView(generic.ObjectListView):
    queryset = OIDCGroupMapping.objects.all()
    table = OIDCGroupMappingTable
    filterset = OIDCGroupMappingFilterSet
    filterset_form = OIDCGroupMappingFilterForm


class OIDCGroupMappingView(generic.ObjectView):
    queryset = OIDCGroupMapping.objects.all()


class OIDCGroupMappingEditView(generic.ObjectEditView):
    queryset = OIDCGroupMapping.objects.all()
    form = OIDCGroupMappingForm


class OIDCGroupMappingDeleteView(generic.ObjectDeleteView):
    queryset = OIDCGroupMapping.objects.all()


class OIDCGroupMappingBulkEditView(generic.BulkEditView):
    queryset = OIDCGroupMapping.objects.all()
    filterset = OIDCGroupMappingFilterSet
    table = OIDCGroupMappingTable
    form = OIDCGroupMappingBulkEditForm


class OIDCGroupMappingBulkImportView(generic.BulkImportView):
    queryset = OIDCGroupMapping.objects.all()
    model_form = OIDCGroupMappingImportForm


class OIDCGroupMappingBulkDeleteView(generic.BulkDeleteView):
    queryset = OIDCGroupMapping.objects.all()
    filterset = OIDCGroupMappingFilterSet
    table = OIDCGroupMappingTable


# --- Config view (singleton pattern) ---

class OIDCGroupSyncConfigView(LoginRequiredMixin, View):
    """Display and edit the singleton sync configuration."""

    def get(self, request):
        config = OIDCGroupSyncConfig.get_solo()
        form = OIDCGroupSyncConfigForm(instance=config)
        return render(request, 'netbox_oidc_group_sync/config.html', {
            'object': config,
            'form': form,
        })

    def post(self, request):
        config = OIDCGroupSyncConfig.get_solo()
        form = OIDCGroupSyncConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "OIDC Group Sync configuration updated.")
            return redirect(reverse('plugins:netbox_oidc_group_sync:config'))
        return render(request, 'netbox_oidc_group_sync/config.html', {
            'object': config,
            'form': form,
        })
