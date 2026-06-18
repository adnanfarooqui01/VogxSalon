from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    booking_reference = serializers.CharField(source='booking.id', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'user',
            'user_name',
            'service',
            'service_name',
            'booking',
            'booking_reference',
            'rating',
            'title',
            'comment',
            'helpful_count',
            'created_at',
            'updated_at',
            'is_verified',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_name',
            'service_name',
            'booking_reference',
            'helpful_count',
            'created_at',
            'updated_at',
            'is_verified',
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)
