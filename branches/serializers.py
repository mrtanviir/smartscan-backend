from rest_framework import serializers
from .models import Branch

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'name_bn', 'code', 'latitude', 'longitude', 'address', 'rating', 'operating_hours', 'image', 'is_active']
