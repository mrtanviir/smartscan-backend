from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'category', 'unit_price', 'cost_price', 'weight_grams', 'is_active')
    search_fields = ('name', 'barcode', 'category')
    list_filter = ('category', 'is_active')
