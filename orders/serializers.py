from rest_framework import serializers
from .models import Order

class OrderCreateSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    items = serializers.ListField(
        child=serializers.DictField()  # [{'product_id': 1, 'quantity': 2}, ...]
    )
    payment_method = serializers.CharField(default="bKash", required=False)
    use_loyalty_points = serializers.BooleanField(default=False, required=False)
