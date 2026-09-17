from django.urls import path
from .views import (
    SendOTPView,
    VerifyOTPView,
    AdminLoginView,
    CustomerProfileView,
    AdminUserManagementView,
    AuditLogListView,
)

urlpatterns = [
    path('auth/send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('customer/profile/', CustomerProfileView.as_view(), name='customer-profile'),
    path('admin/users/', AdminUserManagementView.as_view(), name='admin-users'),
    path('admin/audit-logs/', AuditLogListView.as_view(), name='admin-audit-logs'),
]
