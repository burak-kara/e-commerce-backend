from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import translators as ts
import copy
import numpy as np
import random
from rest_framework.authentication import TokenAuthentication
from django.views.generic.base import TemplateResponseMixin, TemplateView, View
from allauth.account.adapter import get_adapter
from django.shortcuts import redirect
from django.core.mail import send_mail
from .serializers import ItemSerializer, CategorySerializer, UserSerializer, OrderSerializer, ReviewSerializer
from .models import Item, User, Category, Order, Review
from rest_framework import permissions
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice

nltk.download('vader_lexicon')


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
    ordering_fields = ['name', 'price', 'mean_rating']
    filterset_fields = ['category', 'brand', 'mean_rating']
    search_fields = ['name', 'brand', 'description', 'specs']
    filter_backends = [filters.SearchFilter,
                       filters.OrderingFilter, DjangoFilterBackend]
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
    def get_brands_by_category(category):
        try:
            return Item.objects.filter(category__iexact=category).order_by('brand')
        except Item.DoesNotExist:
            raise Http404

    @staticmethod
    def get_all_brands(category):
        try:
            return Item.objects.all().order_by('brand')
        except Item.DoesNotExist:
            raise Http404

    def get(self, request, category, format=None):
        if category == 'all':
            brands = self.get_all_brands(category).values_list(
                'brand', flat=True).distinct()
        else:
            brands = self.get_brands_by_category(
                category).values_list('brand', flat=True).distinct()
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

    def get_item_by_id(self, pk):
        try:
            return Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            raise Http404

    def email_body(self, items, item_counts, total_price, delivery_address):
        items = [j.name for j in [self.get_item_by_id(i) for i in items]]
        counts = item_counts
        result = "Your order has been confirmed!\n\nOrder Detail:\n"

        for i, item in enumerate(items):
            result += str(item) + " X " + str(counts[i]) + "\n"

        result += "\nTotal Price: " + str(total_price) + "₺\n"
        result += "\nDelivery Adress: " + str(delivery_address) + "\n"

        return result

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
            mail_body = self.email_body(
                items, item_counts, total_price, request.data['delivery_address'])
            # print(mail_body)
            send_mail("[Ozu Store] - Your Order Has Been Confirmed 🚀",
                      mail_body,
                      recipient_list=[request.user.email],
                      from_email="info.ozu.store@gmail.com")
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

    @staticmethod
    def email_body(order):

        items = [i.name for i in order.items.all()]
        counts = (order.item_counts).split(",")
        result = "Your order status has been changed for the following order:\n\nOrder Detail:\n"

        for i, item in enumerate(items):
            result += str(item) + " X " + counts[i] + "\n"
        result += "\nTotal Price: " + str(order.total_price) + "₺\n"
        result += "\nDelivery Adress: " + str(order.delivery_address) + "\n"

        result += "\nOrder Status: " + \
                  str(order.STATUS_CHOICES[order.status][1])

        return result

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
            mail_body = self.email_body(order)
            send_mail("[Ozu Store] - Your Order Status Has Been Updated ⌛",
                      mail_body,
                      recipient_list=[order.buyer.email],
                      from_email="info.ozu.store@gmail.com")
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        order = self.get_order(pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    @staticmethod
    def calculate_mean_rating_up(prev_mean, rating, prev_review_count):
        return ((prev_mean * prev_review_count) + rating) / (prev_review_count + 1)

    @staticmethod
    def calculate_mean_rating_down(prev_mean, rating, prev_review_count):
        return ((prev_mean * prev_review_count) - rating) / (prev_review_count - 1)

    def put(self, request, pk, format=None):
        review = self.get_object(pk)
        data = copy.deepcopy(request.data)
        data['item'] = review.item.pk
        data['user'] = review.user.pk

        if int(review.status) == 0 and int(request.data['status']) == 1:
            item = Item.objects.get(pk=review.item.pk)
            updated_review_count = item.review_count + 1
            updated_mean_rating = self.calculate_mean_rating_up(
                item.mean_rating, review.rating, item.review_count)
            item_data = {'mean_rating': updated_mean_rating,
                         'review_count': updated_review_count}
            serializer = ItemSerializer(item, data=item_data)
            if serializer.is_valid():
                serializer.save()

        if int(review.status) == 1 and int(request.data['status']) == 0:
            item = Item.objects.get(pk=review.item.pk)
            updated_review_count = item.review_count - 1
            updated_mean_rating = self.calculate_mean_rating_down(
                item.mean_rating, review.rating, item.review_count)
            item_data = {'mean_rating': updated_mean_rating,
                         'review_count': updated_review_count}
            serializer = ItemSerializer(item, data=item_data)
            if serializer.is_valid():
                serializer.save()

        serializer = ReviewSerializer(review, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        review = self.get_object(pk)

        item = Item.objects.get(pk=review.item.pk)
        updated_review_count = item.review_count - 1
        updated_mean_rating = self.calculate_mean_rating_down(
            item.mean_rating, review.rating, item.review_count)
        item_data = {'mean_rating': updated_mean_rating,
                     'review_count': updated_review_count}
        serializer = ItemSerializer(item, data=item_data)
        if serializer.is_valid():
            serializer.save()

        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def confirm_email(request, key):
    # render function takes argument  - request
    # and return HTML as response
    return "ok"  # render(request, "./home.html")


class RetrieveRatingFromComment(APIView):

    @staticmethod
    def nltk_sentiment(_sentence):
        _nltk_sentiment = SentimentIntensityAnalyzer()
        score = _nltk_sentiment.polarity_scores(_sentence)
        return score

    @staticmethod
    def normalize(value, old_min_max, new_min_max):
        OldMin = old_min_max[0]
        OldMax = old_min_max[1]
        NewMin = new_min_max[0]
        NewMax = new_min_max[1]
        OldValue = value
        OldRange = (OldMax - OldMin)
        NewRange = (NewMax - NewMin)
        return (((OldValue - OldMin) * NewRange) / OldRange) + NewMin

    def post(self, request, format=None):
        try:
            comment = request.data['comment']

            translated_comment = ts.translate_html(comment, translator=ts.google, to_language='en',
                                                   translator_params={})

            sentiment_analysis = self.nltk_sentiment(
                _sentence=translated_comment)

            sentiment_score = sentiment_analysis['compound']
            normalized_sentiment_score = self.normalize(
                sentiment_score, old_min_max=(-1, 1), new_min_max=(1, 5))
            retrieved_rating = round(normalized_sentiment_score)

            data = {'sentiment_score': sentiment_score,
                    'raw_rating': normalized_sentiment_score,
                    'retrieved_rating': retrieved_rating,
                    'translated_comment': translated_comment}

            return Response(data)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# 2-factor Authentication


def get_user_totp_device(self, user, confirmed=None):
    devices = devices_for_user(user, confirmed=confirmed)
    for device in devices:
        if isinstance(device, TOTPDevice):
            return device


class TOTPCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        device = get_user_totp_device(self, user)
        if not device:
            device = user.totpdevice_set.create(confirmed=False)
        url = device.config_url
        return Response(url, status=status.HTTP_201_CREATED)


class TOTPVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, token, format=None):
        user = request.user
        device = get_user_totp_device(self, user)
        if not device == None and device.verify_token(token):
            if not device.confirmed:
                device.confirmed == True
                device.save()
            return Response(True, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_201_CREATED)


class RecommendedProducts(APIView):

    @staticmethod
    def get_previous_purchase_categories(user_id):
        orders = Order.objects.filter(buyer=user_id)

        previous_purchase_categories = list()
        for order in orders:
            for item in order.items.all():
                previous_purchase_categories.append(item.category)
        return previous_purchase_categories

    @staticmethod
    def get_random_recommended_products(previous_purchase_categories):
        frequency = {}
        for item in previous_purchase_categories:
            if item in frequency:
                frequency[item] += 1
            else:
                frequency[item] = 1

        counts = frequency.values()
        normalized_counts = [float(i) / sum(counts) for i in counts]
        chosen_category = np.random.choice(list(frequency.keys()), p=normalized_counts)

        all_from_chosen_category = Item.objects.filter(category__iexact=chosen_category)
        all_from_chosen_category = list(all_from_chosen_category)

        return random.sample(all_from_chosen_category, 1)[0]

    def post(self, request, recommendation_count, format=None):

        user_id = request.user.pk
        previous_purchase_categories = self.get_previous_purchase_categories(user_id)

        recommended_products = list()

        for i in range(recommendation_count):
            recommended_products.append(self.get_random_recommended_products(previous_purchase_categories))

        print(recommended_products)
        recommended_product_ids = [product.pk for product in recommended_products]

        data = {'recommended_product_ids': recommended_product_ids}

        return Response(data)
