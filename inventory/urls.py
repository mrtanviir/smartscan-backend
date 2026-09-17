from django.urls import path
from .views import (
    AdminDashboardKPIView,
    LowStockListView,
    StockTransferView,
    StockAdjustmentView,
    OwnerExecutiveAnalyticsView,
)

urlpatterns = [
    path('admin/dashboard/kpis/', AdminDashboardKPIView.as_view(), name='admin-kpis'),
    path('admin/analytics/branches/', OwnerExecutiveAnalyticsView.as_view(), name='admin-analytics-branches'),
    path('admin/inventory/low-stock/', LowStockListView.as_view(), name='admin-low-stock'),
    path('admin/inventory/adjust/', StockAdjustmentView.as_view(), name='admin-inventory-adjust'),
    path('admin/transfers/', StockTransferView.as_view(), name='stock-transfers'),
    path('admin/transfers/<int:pk>/', StockTransferView.as_view(), name='stock-transfer-update'),
]
