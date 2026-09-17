from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AuditLog

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('phone', 'username', 'email', 'role', 'branch', 'loyalty_points', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'branch')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Profile', {'fields': ('phone', 'role', 'branch', 'loyalty_points')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Profile', {'fields': ('phone', 'role', 'branch', 'loyalty_points')}),
    )

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__phone', 'action', 'details')
