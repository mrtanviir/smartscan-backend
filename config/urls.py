from django.contrib import admin
from django.urls import path, include
from accounts.views import (
    SendOTPView,
    VerifyOTPView,
    AdminLoginView,
    CustomerProfileView,
    CustomerNotificationListView,
    CustomerNotificationMarkReadView,
    AdminUserManagementView,
    AuditLogListView,
)
from products.views import (
    ProductScanView,
    TodayBestOffersView,
    AdminProductListCreateView,
    AdminProductDetailView,
)
from orders.views import (
    CustomerCartListView,
    CustomerCartAddView,
    CustomerCartUpdateView,
    CustomerCartItemDeleteView,
    CustomerCartClearView,
    BillReviewView,
    CheckoutOrderView,
    OrderReceiptView,
    SecurityGateVerifyView,
    ManualOverrideView,
    CustomerOrderHistoryView,
    ActiveGatePassView,
    SubmitFeedbackView,
    ManagerComplaintPortalView,
    SSLCommerzInitiateView,
    SSLCommerzSuccessCallbackView,
    SSLCommerzFailCallbackView,
    SSLCommerzCancelCallbackView,
    SSLCommerzIPNCallbackView,
    SSLCommerzValidateAPIView,
)
from inventory.views import (
    AdminDashboardKPIView,
    LowStockListView,
    StockTransferView,
    StockAdjustmentView,
    OwnerExecutiveAnalyticsView,
)
from branches.views import (
    BranchListView,
    AdminBranchListCreateView,
    AdminBranchDetailView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # 📱 Mobile Customer & Auth APIs
    path('api/v1/auth/send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('api/v1/auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('api/v1/customer/profile/', CustomerProfileView.as_view(), name='customer-profile'),
    
    # 🔔 Customer Notifications APIs
    path('api/v1/customer/notifications/', CustomerNotificationListView.as_view(), name='customer-notifications'),
    path('api/v1/customer/notifications/<int:pk>/read/', CustomerNotificationMarkReadView.as_view(), name='customer-notification-read'),
    path('api/v1/customer/notifications/mark-all-read/', CustomerNotificationMarkReadView.as_view(), name='customer-notifications-mark-all-read'),

    # 🏷️ Today's Best Offers (30 km Radius)
    path('api/v1/products/offers/', TodayBestOffersView.as_view(), name='product-offers'),
    path('api/v1/offers/today/', TodayBestOffersView.as_view(), name='today-offers'),

    # 🧾 Orders, Receipts & Gate Pass
    path('api/v1/customer/orders/', CustomerOrderHistoryView.as_view(), name='customer-orders'),
    path('api/v1/customer/orders/active-pass/', ActiveGatePassView.as_view(), name='active-gate-pass'),
    path('api/v1/customer/orders/<str:order_number>/receipt/', OrderReceiptView.as_view(), name='order-receipt'),
    path('api/v1/customer/orders/<str:order_number>/feedback/', SubmitFeedbackView.as_view(), name='customer-order-feedback'),
    path('api/v1/products/scan/', ProductScanView.as_view(), name='product-scan'),
    path('api/v1/branches/', BranchListView.as_view(), name='branch-list'),

    # 🛒 Customer Smart Cart & Live Sync APIs
    path('api/v1/cart/', CustomerCartListView.as_view(), name='cart-list'),
    path('api/v1/cart/add/', CustomerCartAddView.as_view(), name='cart-add'),
    path('api/v1/cart/update/', CustomerCartUpdateView.as_view(), name='cart-update'),
    path('api/v1/cart/item/<int:product_id>/', CustomerCartItemDeleteView.as_view(), name='cart-item-delete'),
    path('api/v1/cart/clear/', CustomerCartClearView.as_view(), name='cart-clear'),

    # 🧾 Checkout & Bill Review APIs
    path('api/v1/checkout/review/', BillReviewView.as_view(), name='checkout-review'),
    path('api/v1/checkout/create/', CheckoutOrderView.as_view(), name='checkout-create'),

    # 💳 SSLCommerz Payment Gateway APIs
    path('api/v1/payment/sslcommerz/initiate/', SSLCommerzInitiateView.as_view(), name='sslcommerz-initiate'),
    path('api/v1/payment/sslcommerz/success/', SSLCommerzSuccessCallbackView.as_view(), name='sslcommerz-success'),
    path('api/v1/payment/sslcommerz/fail/', SSLCommerzFailCallbackView.as_view(), name='sslcommerz-fail'),
    path('api/v1/payment/sslcommerz/cancel/', SSLCommerzCancelCallbackView.as_view(), name='sslcommerz-cancel'),
    path('api/v1/payment/sslcommerz/ipn/', SSLCommerzIPNCallbackView.as_view(), name='sslcommerz-ipn'),
    path('api/v1/payment/sslcommerz/validate/', SSLCommerzValidateAPIView.as_view(), name='sslcommerz-validate'),

    # 🚪 Exit Security Scale APIs
    path('api/v1/security/verify-pass/', SecurityGateVerifyView.as_view(), name='security-verify'),
    path('api/v1/security/manual-override/', ManualOverrideView.as_view(), name='security-override'),

    # 🖥️ Web Dashboard (Admin, Owner, Manager) APIs
    path('api/v1/auth/admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('api/v1/admin/dashboard/kpis/', AdminDashboardKPIView.as_view(), name='admin-kpis'),
    path('api/v1/admin/analytics/branches/', OwnerExecutiveAnalyticsView.as_view(), name='admin-analytics-branches'),
    path('api/v1/admin/branches/', AdminBranchListCreateView.as_view(), name='admin-branches-list-create'),
    path('api/v1/admin/branches/<int:id>/', AdminBranchDetailView.as_view(), name='admin-branch-detail'),
    path('api/v1/admin/products/', AdminProductListCreateView.as_view(), name='admin-products'),
    path('api/v1/admin/products/<int:id>/', AdminProductDetailView.as_view(), name='admin-product-detail'),
    path('api/v1/admin/inventory/low-stock/', LowStockListView.as_view(), name='admin-low-stock'),
    path('api/v1/admin/inventory/adjust/', StockAdjustmentView.as_view(), name='admin-inventory-adjust'),
    path('api/v1/admin/transfers/', StockTransferView.as_view(), name='stock-transfers'),
    path('api/v1/admin/transfers/<int:pk>/', StockTransferView.as_view(), name='stock-transfer-update'),
    path('api/v1/admin/feedback/', ManagerComplaintPortalView.as_view(), name='admin-feedback-list'),
    path('api/v1/admin/feedback/<int:pk>/', ManagerComplaintPortalView.as_view(), name='admin-feedback-detail'),
    path('api/v1/admin/users/', AdminUserManagementView.as_view(), name='admin-users'),
    path('api/v1/admin/audit-logs/', AuditLogListView.as_view(), name='admin-audit-logs'),
]
