from django.contrib import admin
from .models import Order, OrderFeedback

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'branch', 'total_amount', 'expected_weight_grams', 'status', 'created_at')
    list_filter = ('status', 'branch', 'created_at')
    search_fields = ('order_number', 'customer__phone', 'customer__username')

@admin.register(OrderFeedback)
class OrderFeedbackAdmin(admin.ModelAdmin):
    list_display = ('order', 'customer', 'branch', 'rating', 'status', 'resolved_by', 'created_at')
    list_filter = ('rating', 'status', 'branch', 'created_at')
    search_fields = ('order__order_number', 'customer__phone', 'complaint_text')
