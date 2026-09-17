import hmac
import hashlib
import time
import io
import base64
import json
import qrcode
from django.db import models
from django.conf import settings

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('VERIFIED_PASSED', 'Verified & Gate Passed'),
        ('MANUAL_OVERRIDDEN', 'Manual Overridden'),
    ]
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    loyalty_points_used = models.IntegerField(default=0)
    loyalty_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    expected_weight_grams = models.IntegerField()  # e.g., 7200g
    payment_method = models.CharField(max_length=50, default="bKash")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    security_hash = models.CharField(max_length=255, blank=True)
    qr_code_image = models.TextField(blank=True, null=True)  # Base64 Data URL PNG
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_security_hash(self):
        """HMAC-SHA256 দিয়ে এনক্রিপ্টেড কিউআর পাস জেনারেট করা"""
        payload = f"{self.order_number}:{self.expected_weight_grams}:{int(time.time())}"
        secret_key = settings.SECRET_KEY.encode('utf-8')
        return hmac.new(secret_key, payload.encode('utf-8'), hashlib.sha256).hexdigest()

    def generate_qr_code_base64(self):
        """Generate actual QR Code PNG image as Base64 Data URL"""
        qr_payload = {
            "order_number": self.order_number,
            "weight": self.expected_weight_grams,
            "hash": self.security_hash,
            "branch": self.branch.name,
            "amount": str(self.total_amount)
        }
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(json.dumps(qr_payload))
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F172A", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_str}"

    def __str__(self):
        return f"Order {self.order_number} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    weight_grams = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} for {self.order.order_number}"


class CustomerCartItem(models.Model):
    """
    কাস্টমারের স্মার্ট ট্রলি/কার্ট আইটেম (Server-Side Persistence)
    """
    customer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('customer', 'product', 'branch')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.customer.phone} - {self.product.name} x {self.quantity}"


class OrderFeedback(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='feedback')
    customer = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)  # 1 to 5 Stars
    complaint_text = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='PENDING')  # PENDING, RESOLVED
    resolution_note = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey('accounts.User', related_name='resolved_complaints', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.order.order_number} - {self.rating} Stars ({self.status})"
