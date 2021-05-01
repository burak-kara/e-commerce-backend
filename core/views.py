from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404
import copy

from rest_framework.authentication import TokenAuthentication
from .serializers import ItemSerializer, CategorySerializer, UserSerializer, OrderSerializer, ReviewSerializer
from .models import Item, User, Category, Order, Review


class UserDetail(APIView):
    def get(self, request, format=None):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request, format=None):
        user = request.user
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressDetail(APIView):
    @staticmethod
    def get_user(pk):
        try:
            return User.objects.get(pk=pk)
        except Item.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        user = self.get_user(pk)
        return Response(user.addresses)


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


class ItemSearch(generics.ListAPIView):
    ordering_fields = ['name', 'price']
    filterset_fields = ['category', 'brand']
    search_fields = ['name', 'brand', 'description', 'specs']
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


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


class BrandList(APIView):
    @staticmethod
    def get_object_by_category(category):
        try:
            return Item.objects.filter(category__iexact=category).order_by('brand')
        except Item.DoesNotExist:
            raise Http404

    def get(self, request, category, format=None):
        brands = self.get_object_by_category(category).values_list('brand', flat=True).distinct()
        return Response(brands)


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
                total_price += int(item.price) * item_counts[i]
            return total_price
        except Item.DoesNotExist:
            raise Http404

    @staticmethod
    def to_comma_sep_values(item_counts):
        return ",".join([str(i) for i in item_counts])

    def get(self, request, format=None):
        if request.user.is_sales_manager:
            order = Order.objects.all()
        else:
            order = Order.objects.filter(buyer=request.user.pk)
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        buyer = request.user.pk
        items = [int(i) for i in request.data['items'].keys()]
        item_counts = [int(i) for i in request.data['items'].values()]
        total_price = self.calculate_total_price(items, item_counts)

        serializer = OrderSerializer(
            data={'buyer': buyer, 'items': items, 'item_counts': self.to_comma_sep_values(item_counts),
                  'total_price': total_price, 'delivery_address': request.data['delivery_address']})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetail(APIView):
    """
    Retrieve, update or delete an order instance.
    """

    @staticmethod
    def to_comma_sep_values(item_counts):
        return ",".join([str(i) for i in item_counts])

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
        buyer = order.buyer.pk
        items = [i.pk for i in order.items.all()]
        item_counts = order.item_counts
        total_price = order.total_price

        if 'delivery_address' in request.data.keys():
            delivery_address = request.data['delivery_address']
        else:
            delivery_address = order.delivery_address

        if 'status' in request.data.keys():
            status_ = request.data['status']
        else:
            status_ = order.status

        serializer = OrderSerializer(order, data={'buyer': buyer, 'items': items, 'item_counts': item_counts,
                                                  'total_price': total_price, 'delivery_address': delivery_address,
                                                  'status': status_})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        order = self.get_order(pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Review Implementation..


class ReviewList(APIView):
    """
    List all reviews, or post a new review.
    """

    def get(self, request, format=None):
        review = Review.objects.all()
        serializer = ReviewSerializer(review, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewsOfItem(APIView):
    """
    Retrieve all reviews of an item.
    """

    @staticmethod
    def get_object_by_item(item):
        try:
            return Review.objects.filter(item=item)
        except Review.DoesNotExist:
            raise Http404

    def get(self, request, item, format=None):
        review = self.get_object_by_item(item)
        serializer = ReviewSerializer(review, many=True)
        return Response(serializer.data)


class ReviewDetail(APIView):
    """
    Retrieve, update or delete an item instance.
    """

    @staticmethod
    def get_object(pk):
        try:
            return Review.objects.get(pk=pk)
        except Item.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        review = self.get_object(pk)
        serializer = ReviewSerializer(review)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        review = self.get_object(pk)
        data = copy.deepcopy(request.data)
        data['item'] = review.item.pk
        data['user'] = review.user.pk
        serializer = ReviewSerializer(review, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        review = self.get_object(pk)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
