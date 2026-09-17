from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=100)  # e.g., Dhanmondi
    name_bn = models.CharField(max_length=100, blank=True, null=True)  # e.g., ধানমন্ডি শাখা
    code = models.CharField(max_length=20, unique=True)  # e.g., DHAKA-DHN
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)  # e.g., 4.8
    operating_hours = models.CharField(max_length=100, default="সকাল ১০ - রাত ৯টা")
    image = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Branches'

    def __str__(self):
        return f"{self.name_bn or self.name} ({self.code})"
