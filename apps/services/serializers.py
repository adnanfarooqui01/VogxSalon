from rest_framework import serializers

from .models import ServiceCategory, Service


class ServiceCategorySerializer(serializers.ModelSerializer):
    service_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = [
            'id',
            'name',
            'description',
            'image',
            'is_active',
            'service_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'service_count', 'created_at', 'updated_at']

    def get_service_count(self, obj):
        return obj.services.filter(is_active=True).count()


class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_detail = ServiceCategorySerializer(source='category', read_only=True)

    class Meta:
        model = Service
        fields = [
            'id',
            'category',
            'category_name',
            'category_detail',
            'name',
            'description',
            'price',
            'duration_minutes',
            'image',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'category_name', 'category_detail', 'created_at', 'updated_at']
