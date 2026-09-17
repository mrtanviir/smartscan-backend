from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
    BRANCH_MANAGER = 'BRANCH_MANAGER', 'Branch Manager'
    GATE_SECURITY = 'GATE_SECURITY', 'Gate Security'
    CUSTOMER = 'CUSTOMER', 'Customer'

class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    branch = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    loyalty_points = models.IntegerField(default=0)

    USERNAME_FIELD = 'phone'  # ফোন নম্বর দিয়ে লগইন হবে
    REQUIRED_FIELDS = ['username', 'email']

    def __str__(self):
        return f"{self.phone} ({self.get_role_display()})"


class CustomerNotification(models.Model):
    """
    অ্যাপের কাস্টমার নোটিফিকেশন মডেল (গেটের পাস, স্পেশাল অফার, লয়ালটি পয়েন্ট, কার্ট)
    """
    CATEGORY_CHOICES = [
        ('ALL', 'All'),
        ('ORDER', 'Order & Gate Pass'),
        ('OFFER', 'Special Offers'),
        ('LOYALTY', 'Loyalty Points'),
        ('CART', 'Smart Cart'),
        ('SYSTEM', 'System Alert'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='SYSTEM')
    icon_type = models.CharField(max_length=50, default='SYSTEM')  # GATE_PASS, OFFER, LOYALTY, CART, SYSTEM
    action_type = models.CharField(max_length=50, blank=True, null=True)  # OPEN_GATE_PASS, OPEN_OFFER, OPEN_CART, NONE
    action_data = models.JSONField(blank=True, null=True)  # e.g. {"order_number": "SS753EB1"}
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.phone} - {self.title} ({self.category})"


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)  # e.g. "MANUAL_OVERRIDE", "PRICE_CHANGE"
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_str = self.user.phone if self.user else 'System'
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {user_str}: {self.action}"
