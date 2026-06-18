from rest_framework import serializers

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
