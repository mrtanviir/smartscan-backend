from django.urls import path
from .views import (
    ProductScanView,
    AdminProductListCreateView,
    AdminProductDetailView,
)

urlpatterns = [
    path('products/scan/', ProductScanView.as_view(), name='product-scan-v1'),
    path('scan/', ProductScanView.as_view(), name='product-scan'),
    path('admin/products/', AdminProductListCreateView.as_view(), name='admin-product-list-create'),
    path('admin/products/<int:id>/', AdminProductDetailView.as_view(), name='admin-product-detail'),
]
