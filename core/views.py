from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.http import Http404

from .serializers import ItemSerializer, CategorySerializer, UserSerializer
from .models import Item, User, Category


# TODO token check
class UserDetail(APIView):
	@staticmethod
	def get_user(pk):
		try:
			return User.objects.get(pk=pk)
		except User.DoesNotExist:
			raise Http404

	def get(self, request, pk, format=None):
		user = self.get_user(pk)
		serializer = UserSerializer(user)
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
