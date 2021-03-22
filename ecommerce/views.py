from django.shortcuts import render, redirect
from .models import Item
from django.contrib.auth.models import User
from rest_framework import viewsets
from .serializers import ItemSerializer, UserSerializer


class ItemView(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    queryset = Item.objects.all()


class UserView(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
