from django.db import models

class Inventory(models.Model):
    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    stock_quantity = models.IntegerField(default=0)
    min_safety_threshold = models.IntegerField(default=10)  # Low Stock Alert Limit

    class Meta:
        verbose_name_plural = 'Inventories'
        unique_together = ('branch', 'product')

    def __str__(self):
        return f"{self.branch.name} - {self.product.name} ({self.stock_quantity})"

class StockTransfer(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('IN_TRANSIT', 'In Transit'),
        ('RECEIVED', 'Received'),
        ('REJECTED', 'Rejected'),
    ]
    source_branch = models.ForeignKey('branches.Branch', related_name='transfers_out', on_delete=models.CASCADE)
    dest_branch = models.ForeignKey('branches.Branch', related_name='transfers_in', on_delete=models.CASCADE)
    items_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transfer #{self.id}: {self.source_branch.name} -> {self.dest_branch.name} ({self.status})"

class InventoryMovement(models.Model):
    MOVEMENT_TYPES = [
        ('RECEIPT', 'Stock Received (+Stock)'),
        ('DAMAGE', 'Damaged/Expired (-Stock)'),
        ('TRANSFER_OUT', 'Transferred to other branch (-Stock)'),
        ('SALE', 'Customer Checkout (-Stock)'),
    ]
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    remarks = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inventory.product.name} - {self.movement_type} ({self.quantity})"
