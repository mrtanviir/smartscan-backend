from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'barcode', 'name', 'name_bn', 'category', 'unit_price', 'cost_price', 'unit_info', 'image', 'weight_grams', 'discount_amount', 'is_active']
