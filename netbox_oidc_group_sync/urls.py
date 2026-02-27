from django.urls import path
from netbox.views.generic import ObjectChangeLogView
from . import models, views

urlpatterns = [
    # Group Mappings
    path('mappings/', views.OIDCGroupMappingListView.as_view(), name='oidcgroupmapping_list'),
    path('mappings/add/', views.OIDCGroupMappingEditView.as_view(), name='oidcgroupmapping_add'),
    path('mappings/import/', views.OIDCGroupMappingBulkImportView.as_view(), name='oidcgroupmapping_import'),
    path('mappings/edit/', views.OIDCGroupMappingBulkEditView.as_view(), name='oidcgroupmapping_bulk_edit'),
    path('mappings/delete/', views.OIDCGroupMappingBulkDeleteView.as_view(), name='oidcgroupmapping_bulk_delete'),
    path('mappings/<int:pk>/', views.OIDCGroupMappingView.as_view(), name='oidcgroupmapping'),
    path('mappings/<int:pk>/edit/', views.OIDCGroupMappingEditView.as_view(), name='oidcgroupmapping_edit'),
    path('mappings/<int:pk>/delete/', views.OIDCGroupMappingDeleteView.as_view(), name='oidcgroupmapping_delete'),
    path('mappings/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='oidcgroupmapping_changelog', kwargs={'model': models.OIDCGroupMapping}),

    # Config (singleton)
    path('config/', views.OIDCGroupSyncConfigView.as_view(), name='config'),
]
