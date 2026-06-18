from rest_framework import serializers

from .models import ServiceCategory, Service, ServiceStep, Package


class ServiceCategorySerializer(serializers.ModelSerializer):
    service_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = [
            'id',
            'name',
            'description',
            'icon',
            'gender',
            'order',
            'is_active',
            'show_on_home',
            'service_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'service_count', 'created_at', 'updated_at']

    def get_service_count(self, obj):
        return obj.services.filter(is_available=True).count()


class ServiceStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStep
        fields = ['id', 'step_number', 'title', 'description']
        read_only_fields = ['id']


class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_gender = serializers.CharField(source='category.gender', read_only=True)
    steps = ServiceStepSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = [
            'id',
            'category',
            'category_name',
            'category_gender',
            'name',
            'description',
            'price',
            'duration_minutes',
            'preview_image',
            'detail_image',
            'service_type',
            'is_available',
            'steps',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'category_name', 'category_gender', 'steps', 'created_at', 'updated_at']


class PackageSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    service_ids = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        write_only=True,
        many=True,
        source='services'
    )

    class Meta:
        model = Package
        fields = [
            'id',
            'name',
            'description',
            'services',
            'service_ids',
            'package_price',
            'image',
            'gender',
            'is_available',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'services', 'created_at', 'updated_at']
