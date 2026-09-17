from django.urls import path
from .views import (
    BranchListView,
    AdminBranchListCreateView,
    AdminBranchDetailView,
)

urlpatterns = [
    path('branches/', BranchListView.as_view(), name='branch-list'),
    path('admin/branches/', AdminBranchListCreateView.as_view(), name='admin-branches-list-create'),
    path('admin/branches/<int:id>/', AdminBranchDetailView.as_view(), name='admin-branch-detail'),
]
