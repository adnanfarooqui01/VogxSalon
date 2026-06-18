from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from .models import CustomUser, OTPLog


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'phone',
            'name',
            'email',
            'password',
            'is_active',
            'is_staff',
            'is_employee',
            'date_joined',
            'updated_at',
        ]
        read_only_fields = ['id', 'is_active', 'is_staff', 'date_joined', 'updated_at']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class OTPLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPLog
        fields = ['id', 'phone', 'date', 'count', 'last_sent']
        read_only_fields = ['id', 'date', 'last_sent']


class PhoneLoginSerializer(serializers.Serializer):
    """Serialize phone login request and generate/send OTP"""
    phone = serializers.CharField(max_length=15)
    
    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone must contain only digits")
        if len(value) < 10 or len(value) > 15:
            raise serializers.ValidationError("Phone must be 10-15 digits")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Serialize OTP verification and return authentication token"""
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6, min_length=4)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone must contain only digits")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serialize user profile for authenticated users"""
    
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'phone',
            'name',
            'email',
            'is_employee',
            'date_joined',
            'updated_at',
        ]
        read_only_fields = ['id', 'phone', 'date_joined', 'updated_at']


class LogoutSerializer(serializers.Serializer):
    """Serialize logout request"""
    pass
