from decimal import Decimal

from rest_framework import serializers

from logging import getLogger

logger = getLogger('django')


class TransactionSerializer(serializers.Serializer):
    tx_code = serializers.CharField(required=True)
    tx_type = serializers.CharField(required=True)
    from_user = serializers.CharField(required=True)
    to_user = serializers.CharField(required=False)
    status = serializers.CharField(required=True)
    amount = serializers.CharField(required=True)
    fee = serializers.CharField(required=False)
    currency = serializers.CharField(required=True)
    company = serializers.CharField(required=True)
    created = serializers.CharField(required=True)
    note = serializers.CharField(required=False)
    metadata = serializers.JSONField(required=False)


class UserAccountSerializer(serializers.Serializer):
    user_id = serializers.CharField(required=True)
    metadata = serializers.JSONField(required=False)


class AddAssetSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    issuer = serializers.CharField(required=True)
    metadata = serializers.JSONField(required=False)