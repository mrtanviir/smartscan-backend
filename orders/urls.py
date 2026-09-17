from django.urls import path
from .views import (
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

urlpatterns = [
    # 🛒 Customer Smart Cart & Live Sync APIs
    path('cart/', CustomerCartListView.as_view(), name='cart-list'),
    path('cart/add/', CustomerCartAddView.as_view(), name='cart-add'),
    path('cart/update/', CustomerCartUpdateView.as_view(), name='cart-update'),
    path('cart/item/<int:product_id>/', CustomerCartItemDeleteView.as_view(), name='cart-item-delete'),
    path('cart/clear/', CustomerCartClearView.as_view(), name='cart-clear'),

    # Customer Checkout & Bill Review APIs
    path('checkout/review/', BillReviewView.as_view(), name='checkout-review'),
    path('checkout/create/', CheckoutOrderView.as_view(), name='checkout-create'),
    
    # SSLCommerz Payment Gateway APIs
    path('payment/sslcommerz/initiate/', SSLCommerzInitiateView.as_view(), name='sslcommerz-initiate'),
    path('payment/sslcommerz/success/', SSLCommerzSuccessCallbackView.as_view(), name='sslcommerz-success'),
    path('payment/sslcommerz/fail/', SSLCommerzFailCallbackView.as_view(), name='sslcommerz-fail'),
    path('payment/sslcommerz/cancel/', SSLCommerzCancelCallbackView.as_view(), name='sslcommerz-cancel'),
    path('payment/sslcommerz/ipn/', SSLCommerzIPNCallbackView.as_view(), name='sslcommerz-ipn'),
    path('payment/sslcommerz/validate/', SSLCommerzValidateAPIView.as_view(), name='sslcommerz-validate'),

    # Orders, Receipts & Gate Pass APIs
    path('customer/orders/', CustomerOrderHistoryView.as_view(), name='customer-orders'),
    path('customer/orders/active-pass/', ActiveGatePassView.as_view(), name='active-gate-pass'),
    path('customer/orders/<str:order_number>/receipt/', OrderReceiptView.as_view(), name='order-receipt'),
    path('customer/orders/<str:order_number>/feedback/', SubmitFeedbackView.as_view(), name='customer-order-feedback'),

    # Security & Staff APIs
    path('security/verify-pass/', SecurityGateVerifyView.as_view(), name='security-verify'),
    path('security/manual-override/', ManualOverrideView.as_view(), name='security-override'),

    # Manager Complaints Admin APIs
    path('admin/feedback/', ManagerComplaintPortalView.as_view(), name='admin-feedback-list'),
    path('admin/feedback/<int:pk>/', ManagerComplaintPortalView.as_view(), name='admin-feedback-detail'),
]
