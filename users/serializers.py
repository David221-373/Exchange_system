from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "address",
            "is_active",
        ]
        read_only_fields = ["id"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "phone", "address", "password"]

    def create(self, validated_data):
        user = User(**{k: v for k, v in validated_data.items() if k != "password"})
        user.role = "client"
        user.set_password(validated_data["password"])
        user.save()
        return user
