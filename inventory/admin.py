from django.contrib import admin
from .models import Inventory, StockTransfer, InventoryMovement

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('branch', 'product', 'stock_quantity', 'min_safety_threshold')
    list_filter = ('branch', 'product')
    search_fields = ('product__name', 'product__barcode', 'branch__name')

@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_branch', 'dest_branch', 'items_count', 'status', 'created_at')
    list_filter = ('status', 'source_branch', 'dest_branch')

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'movement_type', 'quantity', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('inventory__product__name', 'remarks')
