from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = (
            'name', 'description', 'seller'
        )
