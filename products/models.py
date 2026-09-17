from django.db import models

class Product(models.Model):
    barcode = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)  # e.g. Mini-ket Rice - 5kg
    name_bn = models.CharField(max_length=255, blank=True, null=True)  # e.g. মিনিকেট চাল - ৫ কেজি
    category = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # e.g. 500.00
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)  # e.g. 420.00
    unit_info = models.CharField(max_length=50, blank=True, default="৳১০০/কেজি")  # e.g. ৳১০০/কেজি
    image = models.CharField(max_length=500, blank=True, null=True)
    weight_grams = models.IntegerField(help_text="Product weight in grams")  # e.g., 5000 for 5kg
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.barcode})"
