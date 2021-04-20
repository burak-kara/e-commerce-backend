from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.http import Http404

from rest_framework.authentication import TokenAuthentication
from .serializers import ItemSerializer, CategorySerializer, UserSerializer, OrderSerializer
from .models import Item, User, Category, Order


class UserDetail(APIView):
    def get(self, request, format=None):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class ItemList(APIView):
    """
    List all items, or create a new item.
    """

    def get(self, request, format=None):
        item = Item.objects.all()
        serializer = ItemSerializer(item, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemDetail(APIView):
    """
    Retrieve, update or delete an item instance.
    """

    @staticmethod
    def get_object(pk):
        try:
            return Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        item = self.get_object(pk)
        serializer = ItemSerializer(item)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        item = self.get_object(pk)
        serializer = ItemSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        item = self.get_object(pk)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ItemsByCategory(APIView):
    """
    Retrieve an item instance.
    """

    @staticmethod
    def get_object_by_category(category):
        try:
            return Item.objects.filter(category__iexact=category)
        except Item.DoesNotExist:
            raise Http404

    def get(self, request, category, format=None):
        item = self.get_object_by_category(category)
        serializer = ItemSerializer(item, many=True)
        return Response(serializer.data)


class CategoryList(APIView):
    """
    List all categories, or create a new category.
    """

    def get(self, request, format=None):
        category = Category.objects.all()
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderList(APIView):
    """
    List all orders, or create a new one.
    """

    @staticmethod
    def calculate_total_price(items, item_counts):
        try:
            total_price = 0
            for i, pk in enumerate(items):
                item = Item.objects.get(pk=pk)
                print("------------")
                print(int(item.price))
                print(item_counts[i])
                print(int(item.price) * item_counts[i])
                print("------------")
                total_price += int(item.price) * item_counts[i]
            return total_price
        except Item.DoesNotExist:
            raise Http404

    @staticmethod
    def to_comma_sep_values(item_counts):
        return ",".join([str(i) for i in item_counts])

    def get(self, request, format=None):
        order = Order.objects.all()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        buyer = request.user.pk
        items = [int(i) for i in request.data['items'].keys()]
        item_counts = [int(i) for i in request.data['items'].values()]
        total_price = self.calculate_total_price(items, item_counts)

        serializer = OrderSerializer(
            data={'buyer': buyer, 'items': items, 'item_counts': self.to_comma_sep_values(item_counts),
                  'total_price': total_price, 'is_accepted': request.data['is_accepted']})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetail(APIView):
    """
    Retrieve, update or delete an order instance.
    """

    @staticmethod
    def get_order(pk):
        try:
            return Order.objects.get(pk=pk)
        except Item.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        order = self.get_order(pk)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        order = self.get_order(pk)

        items = [int(i) for i in request.data['items'].keys()]
        item_counts = [int(i) for i in request.data['items'].values()]
        total_price = self.calculate_total_price(items, item_counts)

        serializer = OrderSerializer(order, data={'items': items,
                                                  'item_counts': self.to_comma_sep_values(item_counts),
                                                  'total_price': total_price,
                                                  'is_accepted': request.data['is_accepted']})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        order = self.get_order(pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
