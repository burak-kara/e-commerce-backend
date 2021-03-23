from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ItemSerializer
from django.contrib.auth.models import User
from .models import Item


class ItemView(APIView):
    def get(self, request, *args, **kwargs):
        query_set = Item.objects.all()
        serializer = ItemSerializer(query_set, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = ItemSerializer(data=request.data)
        print(serializer)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
