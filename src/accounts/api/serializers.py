import secrets
import uuid
from django.conf import settings
from django.contrib.auth import authenticate
from django_email_verification import sendConfirm
from rest_framework import serializers
from django.utils import timezone

from ..models import (Account, PasswordResetRequestModel)


class PublicAccountDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = (
            "unique_identifier",
            "username",
            "legacy_id",
            "is_verified",
        )


class RegisterAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ("unique_identifier", "username", "password", "email")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        """Create and return a new account"""
        account = Account.objects.create_user(**validated_data)
        if settings.REQUIRE_EMAIL_CONFIRMATION:
            sendConfirm(account)
        return account


class LoginWithCredentialsSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"})

    def validate(self, data):
        account = authenticate(username=data["email"], password=data["password"])
        if account is None:
            raise serializers.ValidationError("Unable to login with provided credentials.")
        if not account.is_active:
            raise serializers.ValidationError(
                "This account hasn't done the mail confirmation step or has been disabled."
            )
        return account


class UpdateAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ("username", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def update(self, instance, validated_data):
        old_email = instance.email
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.set_password(validated_data.get("password", instance.password))

        if old_email != instance.email and settings.REQUIRE_EMAIL_CONFIRMATION:
            instance.is_active = False
            sendConfirm(instance)

        instance.save()
        return instance


class VerifyAccountSerializer(serializers.Serializer):
    unique_identifier = serializers.CharField()
    verification_token = serializers.UUIDField()

    def validate(self, data):
        account = Account.objects.get(unique_identifier=data["unique_identifier"])

        data_token = data["verification_token"]
        account_token = account.verification_token

        if account_token != data_token:
            raise serializers.ValidationError(
                "Verification token seems invalid or maybe outdated. Try requesting a new one."
            )
        return account

class ChangePasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ("password",)
        extra_kwargs = {"password": {"write_only": True}}
    

class ChangePasswordRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordResetRequestModel
        fields = ["email"]

    email = serializers.EmailField()

    def validate(self, data):
        email = data.get("email")
        account = Account.objects.filter(email=email).first()
        # Note: Make this silently fail later; users don't need to know about this.
        if account is None:
            raise serializers.ValidationError("Account with this email doesn't exist.")

        # Create a new instance of PasswordResetRequestModel using the account's verification token
        token = secrets.token_urlsafe(32)
        new_model_data = {"token": token, "account": account, "created_at": timezone.now() + timezone.timedelta(minutes=35)}
        return new_model_data
    
    def create(self, validated_data):
        print(validated_data)
        reset_request = PasswordResetRequestModel.objects.create(**validated_data)
        return reset_request