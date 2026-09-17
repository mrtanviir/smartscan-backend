from django.contrib import admin
from .models import Branch

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'latitude', 'longitude', 'is_active')
    search_fields = ('name', 'code', 'address')
    list_filter = ('is_active',)
