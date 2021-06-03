from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics
from rest_framework import filters
from django_filters import FilterSet, NumberFilter
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
from .serializers import ItemSerializer, CategorySerializer, UserSerializer, OrderSerializer, ReviewSerializer, \
    CampaignSerializer, AdvertisementSerializer, UserPrivilegeSerializer, WalletSerializer, UserSelectSerializer
from .models import Item, User, Category, Order, Review, Campaign, Advertisement
from rest_framework import permissions
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.conf import settings
# Stats
from datetime import date
# Blockchain
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
import json
import re
# Campaigns
from rest_framework.exceptions import ValidationError

private_key_master = settings.PRIVATE_KEY
public_key_master = '0xB78DFDdF8af06485b5358ad98950119F6f270AE4'

contract_address = '0x1781684a1A5eff097C631E227d654a3470842e45'


def initialize_chain_connection():
    w3 = Web3(Web3.HTTPProvider(
        "https://data-seed-prebsc-2-s1.binance.org:8545/"))  # "1-s2 provider has the most uptime" - Emir
    # might cause errors lul
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


w3 = initialize_chain_connection()
contract_abi_directory = './static/blockchain/contract_abi.json'

f = open(contract_abi_directory)
temp_abi = json.load(f)
contract = w3.eth.contract(address=contract_address, abi=temp_abi)


def pay(recipient_address, amount, payee_address=public_key_master):
    private_key_master = '95b3eb7b43f5352ad277b7260438ed8f13ab14deaa9c5eee77352cea1a4ce0d6'
    w3 = initialize_chain_connection()
    txn = contract.functions.transfer(recipient_address, amount).buildTransaction({'from': payee_address,
                                                                                   'nonce': w3.eth.getTransactionCount(
                                                                                       payee_address)})
    signed_txn = w3.eth.account.sign_transaction(
        txn, private_key=private_key_master)
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    txn_id = w3.eth.waitForTransactionReceipt(txn_hash)['transactionHash']
    return txn_id.hex()


nltk.download('vader_lexicon')


def initialize_chain_connection():
    # 1-s2 provider has the most uptime
    w3 = Web3(Web3.HTTPProvider(
        "https://data-seed-prebsc-2-s1.binance.org:8545/"))
    # might cause errors lul
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


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


class Funding(APIView):
    def get(self, request, format=None):
        pk = request.user.pk
        user_obj = User.objects.get(pk=pk)
        queried_balance = self.update_balance(user_obj)
        updated_data = {'balance': queried_balance,
                        'username': user_obj.username,
                        'first_name': user_obj.first_name,
                        'last_name': user_obj.last_name,
                        'wallet_address': user_obj.wallet_address,
                        'private_wallet_address': user_obj.private_wallet_address}
        serializer = WalletSerializer(user_obj, data=updated_data)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(status=status.HTTP_200_OK)

    def post(self, request, format=None):
        amt = request.data.get("amt")
        amt = int(amt)
        total_supply = contract.functions.balanceOf(public_key_master).call()
        if amt <= total_supply:
            user_email = request.user.email
            user_obj = User.objects.get(email=user_email)
            wallet_address = user_obj.wallet_address
            amount = amt
            transaction_id = self.transfer_tokens(amount, wallet_address)
            new_balance = self.update_balance(user_obj)
            updated_data = {'balance': new_balance,
                            'username': user_obj.username,
                            'first_name': user_obj.first_name,
                            'last_name': user_obj.last_name,
                            'wallet_address': user_obj.wallet_address,
                            'private_wallet_address': user_obj.private_wallet_address}
            serializer = WalletSerializer(user_obj, data=updated_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def pay(recipient_address, amount, payee_address=public_key_master):
        w3 = initialize_chain_connection()
        txn = contract.functions.transfer(recipient, amount).buildTransaction({'from': payee_address,
                                                                               'nonce': w3.eth.getTransactionCount(
                                                                                   payee_address)})
        signed_txn = w3.eth.account.sign_transaction(
            txn, private_key=private_key_master)
        txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        txn_id = w3.eth.waitForTransactionReceipt(txn_hash)['transactionHash']
        return txn_id.hex()

    @staticmethod
    def transfer_tokens(amount, recipient_address):
        try:
            amount = amount
            transactionID = pay(recipient_address, amount)
            return transactionID
        except:
            raise Http404

    @staticmethod
    def update_balance(userObj):
        try:
            recipient = userObj
            new_balance = contract.functions.balanceOf(
                recipient.wallet_address).call()
            recipient.balance = new_balance
            return new_balance
        except User.DoesNotExist:
            raise Http404


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


class GetAllUsers(APIView):

    def get(self, request, format=None):
        filered_user_objects = User.objects.all().filter(
            is_admin=False).filter(is_superuser=False)
        allUsersSerializer = UserSelectSerializer(
            filered_user_objects, many=True)
        return Response(allUsersSerializer.data)


class updateUserMgrChange(APIView):

    @staticmethod
    def get_user(pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        selected_user = self.get_user(pk)
        UserSelectSerializer = UserPrivilegeSerializer(selected_user)
        return Response(UserSelectSerializer.data)

    def put(self, request, pk):
        is_sales_mgr = request.data.get("is_sales_manager")
        is_product_mgr = request.data.get("is_product_manager")
        selected_user = self.get_user(pk)
        modified_privilege = {'username': selected_user.username,
                              'is_sales_manager': is_sales_mgr,
                              'is_product_manager': is_product_mgr}
        serializer = UserPrivilegeSerializer(
            selected_user, data=modified_privilege)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class ItemsByRating(APIView):
    """
    Retrieve an item by rating.
    """

    @staticmethod
    def get_object_by_rating(rating, brand, category):
        try:
            return Item.objects.filter(mean_rating=rating)
        except Item.DoesNotExist:
            raise Http404

    def get(self, request, rating, format=None):
        item = self.get_object_by_rating(rating, brand, category)
        serializer = ItemSerializer(item, many=True)
        return Response(serializer.data)


class RangeFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        price_lt = int(request.GET.get('price_lt', '-1'))
        price_gt = int(request.GET.get('price_gt', '-1'))
        rating_lt = int(request.GET.get('rating_lt', '-1'))
        rating_gt = int(request.GET.get('rating_gt', '-1'))
        if price_lt != -1:
            queryset = queryset.filter(price__lte=price_lt)
        if price_gt != -1:
            queryset = queryset.filter(price__gte=price_gt)
        if rating_lt != -1:
            queryset = queryset.filter(mean_rating__lte=rating_lt)
        if rating_gt != -1:
            queryset = queryset.filter(mean_rating__gte=rating_gt)
        return queryset


class ItemSearch(generics.ListAPIView):
    ordering_fields = ['name', 'price', 'mean_rating']
    filterset_fields = ['category', 'brand', 'mean_rating', 'price']
    search_fields = ['name', 'brand', 'description', 'specs']
    filter_backends = [filters.SearchFilter,
                       filters.OrderingFilter, RangeFilterBackend, DjangoFilterBackend]
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
    def apply_campaign(campaigns, count, full_price):
        result = 0
        for campaign in campaigns:
            # Buy X get Y free
            if int(campaign.campaign_amount) == 0:
                if count % int(campaign.campaign_x) == 0:
                    result += int(full_price) * count
                    result *= 1 - \
                        ((int(campaign.campaign_x) - int(campaign.campaign_y)
                          ) / int(campaign.campaign_x))
                else:
                    result += int(full_price) * count
            # Buy X and get M percent off of Y amount
            elif campaign.campaign_y != 0:
                if count % (int(campaign.campaign_x) + int(campaign.campaign_y)) == 0:
                    result += int(full_price) * \
                        int(campaign.campaign_x)
                    result += (int(full_price) * int(campaign.campaign_y)
                               ) * (1 - (int(campaign.campaign_y) / 100))
                else:
                    result += int(full_price) * count
            # Percentage Discount
            else:
                result += int(full_price) * count
                result *= ((100 -
                            int(campaign.campaign_amount)) / 100)

        return result

    def calculate_total_price(self, items, item_counts):
        try:
            total_price = 0

            for i, pk in enumerate(items):

                item = Item.objects.get(pk=pk)
                campaigns = item.campaign.all()

            if len(campaigns) == 0:
                total_price = 0
                for i, pk in enumerate(items):
                    item = Item.objects.get(pk=pk)
                    total_price += int(item.price) * item_counts[i]

            else:
                total_price += self.apply_campaign(campaigns,
                                                   item_counts[i],
                                                   item.price)

            return round(total_price, 2)
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

        result += "\nTotal Price: " + str(total_price) + "OzuToken\n"
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

        user_obj = User.objects.get(pk=buyer)
        buyer_wallet = user_obj.wallet_address
        buyer_balance = float(self.check_customer_balance(buyer_wallet))
        print(buyer_balance, total_price)
        if buyer_balance >= float(total_price):
            try:
                transaction_id = self.customer_pay(
                    int(total_price), user_obj)

                new_balance = self.check_customer_balance(buyer_wallet)
                updated_data = {'balance': new_balance,
                                'username': user_obj.username,
                                'first_name': user_obj.first_name,
                                'last_name': user_obj.last_name,
                                'wallet_address': user_obj.wallet_address,
                                'private_wallet_address': user_obj.private_wallet_address}
                buyer_wallet_serializer = WalletSerializer(
                    user_obj, data=updated_data)
                if serializer.is_valid() & buyer_wallet_serializer.is_valid():
                    buyer_wallet_serializer.save()
                    serializer.save()
                    mail_body = self.email_body(
                        items, item_counts, total_price, request.data['delivery_address'])
                    send_mail("[Ozu Store] - Your Order Has Been Confirmed 🚀",
                              mail_body,
                              recipient_list=[request.user.email],
                              from_email="info.ozu.store@gmail.com")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(e)
                payment_error_dict = {
                    'Error': "Something went wrong while making the payment"}
                payment_error_json = json.dumps(payment_error_dict)
                return Response(payment_error_json, status=status.HTTP_400_BAD_REQUEST)
        error_dict = {'total_price': total_price,
                      'wallet_balance': self.check_customer_balance(buyer_wallet)}
        return Response(status=status.HTTP_400_BAD_REQUEST, data=error_dict)

    @staticmethod
    def check_customer_balance(wallet_address):
        user_wallet_address = wallet_address
        balance = int(contract.functions.balanceOf(user_wallet_address).call())
        return balance

    @staticmethod
    def customer_pay(amount, payee, recipient_address=public_key_master):
        w3 = initialize_chain_connection()
        recipient = recipient_address
        payee_address = payee.wallet_address
        payee_private_key = payee.private_wallet_address
        txn = contract.functions.transfer(recipient, amount).buildTransaction({'from': payee_address,
                                                                               'nonce': w3.eth.getTransactionCount(
                                                                                   payee_address)})
        signed_txn = w3.eth.account.sign_transaction(
            txn, private_key=payee_private_key)
        txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        txn_id = w3.eth.waitForTransactionReceipt(txn_hash)['transactionHash']
        return txn_id.hex()

    @staticmethod
    def update_balance(pk):
        try:
            recipient = User.objects.get(pk=userName)
            new_balance = contract.functions.balanceOf(
                recipient.wallet_address).call()
            recipient.balance = new_balance
            return new_balance
        except User.DoesNotExist:
            raise status.HTTP_400_BAD_REQUEST


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
        result += "\nTotal Price: " + str(order.total_price) + "OzuToken\n"
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
        except Review.DoesNotExist:
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
        is_successfully_translated = True

        comment = request.data['comment']

        try:
            translated_comment = ts.translate_html(
                comment, translator=ts.alibaba)
            translated_comment = re.sub('<[^>]+>', '', translated_comment)

        except:
            is_successfully_translated = False
            translated_comment = comment

        try:
            sentiment_analysis = self.nltk_sentiment(
                _sentence=translated_comment)

            sentiment_score = sentiment_analysis['compound']
            normalized_sentiment_score = self.normalize(
                sentiment_score, old_min_max=(-1, 1), new_min_max=(1, 5))
            retrieved_rating = round(normalized_sentiment_score)

            data = {'sentiment_score': sentiment_score,
                    'raw_rating': normalized_sentiment_score,
                    'retrieved_rating': retrieved_rating,
                    'translated_comment': translated_comment,
                    'is_successfully_translated': is_successfully_translated}

            return Response(data)
        except Exception as e:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={'exception': str(e)})


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
        chosen_category = np.random.choice(
            list(frequency.keys()), p=normalized_counts)

        all_from_chosen_category = Item.objects.filter(
            category__iexact=chosen_category)
        all_from_chosen_category = list(all_from_chosen_category)

        return random.sample(all_from_chosen_category, 1)[0]

    def post(self, request, recommendation_count, format=None):

        user_id = request.user.pk

        if len(Order.objects.filter(buyer=user_id)) <= 0:
            return Response({})

        previous_purchase_categories = self.get_previous_purchase_categories(
            user_id)

        recommended_products = list()

        for i in range(recommendation_count):
            recommended_products.append(
                self.get_random_recommended_products(previous_purchase_categories))

        recommended_product_ids = [
            product.pk for product in recommended_products]

        data = {'recommended_product_ids': recommended_product_ids}

        return Response(data)


# Charts and stats


class StatisticDetail(APIView):
    @staticmethod
    def create_stats(in_data):

        result = {}  # Holds stats
        result[in_data['date'][0]] = []  # Create an empty entry for day one

        # day by day sold item count
        item_count_day = {}
        daily_income = 0
        for i, items in enumerate(in_data["items"]):
            # Add every price to daily income
            daily_income += in_data['total_price'][i]

            # Once a day passes
            if in_data['date'][i] not in result.keys():
                # Sort the distionary by value
                item_count_day = {k: v for k, v in sorted(
                    item_count_day.items(), key=lambda item: item[1], reverse=True)}

                # Add stats to days
                result[in_data['date'][i - 1]].append(item_count_day)
                result[in_data['date'][i - 1]].append(daily_income)

                # Add an empty slot for a new day
                result[in_data['date'][i]] = []

                # Reset stats
                item_count_day = {}
                daily_income = 0

            # Split orders by item and add up item counts
            for j, item in enumerate(items):

                # Create an entry for an item if not in dictionary
                if item[0] not in item_count_day.keys():
                    item_count_day[item[0]] = int(
                        in_data['item_counts'][i].split(",")[j])

                # Add how much it has been ordered in current order
                else:
                    item_count_day[item[0]
                                   ] += int(in_data['item_counts'][i].split(",")[j])
                # Sort the distionary by value
                item_count_day = {k: v for k, v in sorted(
                    item_count_day.items(), key=lambda item: item[1], reverse=True)}
        # Add todays stats
        result[in_data['date'][i]].append(item_count_day)
        result[in_data['date'][i - 1]].append(daily_income)

        # Refactor data
        refactored_result = {
            "last_5_total_revenue": {
                "days": [],
                "revenue": {
                    "name": 'Total Revenue',
                    "data": []
                }
            },
            "top_5_sold_products_all_time": {
                "products": [],
                "counts": {
                    "name": 'Total Sold Count',
                    "data": []
                }
            },
            "top_5_sold_products_all_time_shares": [],
            "total_sold_product_counts_5_days": {
                "days": [],
                "revenue": {
                    "name": "Total Sold Product Count",
                    "data": []
                }
            }
        }
        all_sales = {}

        for key in result.keys():
            data = result[key]
            refactored_result["last_5_total_revenue"]["days"].append(key)
            refactored_result["total_sold_product_counts_5_days"]["days"].append(
                key)
            refactored_result["last_5_total_revenue"]["revenue"]["data"].append(
                data[1])
            refactored_result["total_sold_product_counts_5_days"]["revenue"]["data"].append(
                sum(list(data[0].values())))

            for item in data[0].keys():
                if item not in all_sales.keys():
                    all_sales[item] = int(data[0][item])
                else:
                    all_sales[item] += int(data[0][item])

        all_sales = {k: v for k, v in sorted(
            all_sales.items(), key=lambda item: item[1], reverse=True)}

        top_5_sales = list(all_sales.values())[:5]
        top_5_sale_product = [Item.objects.get(
            pk=i).name for i in list(all_sales.keys())[:5]]

        refactored_result["top_5_sold_products_all_time"]["products"] = top_5_sale_product
        refactored_result["top_5_sold_products_all_time"]["counts"]["data"] = top_5_sales

        top_5_sales_shares = [round(i / sum(top_5_sales), 2)
                              for i in top_5_sales]
        for item, share in zip(top_5_sale_product, top_5_sales_shares):
            refactored_result["top_5_sold_products_all_time_shares"].append(
                {
                    "name": item,
                    "share": share
                }
            )

        return refactored_result

    def get(self, request, format=None):
        orders_in_frame = []  # Will store every order inside the given timeframe

        # Only sales manager can access stats
        if request.user.is_sales_manager:
            # Get every order filter by date later
            orders = Order.objects.all()
            for order in orders:
                orders_in_frame.append(order)

        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Create a dictionary with orders inside the frame and their important
        # attributes
        result = {'id': [],
                  'items': [],
                  'item_counts': [],
                  'total_price': [],
                  'date': []}

        for order in orders_in_frame:
            for key in result.keys():
                result[key].append(getattr(order, key))

        # Swap item object references to names and ids and
        # convert dates to string to return a response
        items_ids = []
        date_strs = []
        for item, temp_date in zip(result['items'], result['date']):
            temp_item = [(j.id, j.name) for j in item.all()]
            date_strs.append(str(temp_date))
            items_ids.append(temp_item)
        result['items'] = items_ids
        result['date'] = date_strs

        # Example date: "2021-05-21"
        # For every date 0th index is day by day sold item count
        # For every date 1st index is day by day revenue
        # Item counts are sorted so top X can be obtained
        data = self.create_stats(result)

        return Response(data)


# Campaign


class CampaignDetail(APIView):

    @staticmethod
    def get_object(pk):
        try:
            return Campaign.objects.get(pk=pk)
        except Campaign.DoesNotExist:
            raise Http404

    def delete(self, request, uuid, format=None):
        if request.user.is_sales_manager:
            Campaign.objects.get(id=uuid).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    def get(self, request, uuid, format=None):
        if request.user.is_sales_manager:
            campaign = self.get_object(uuid)
            serializer = CampaignSerializer(campaign)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class CampaignList(APIView):
    @staticmethod
    def name_description(x, y, amount):
        if int(amount) == 0:
            name = "Buy {} Get {} Free".format(str(x), str(y))
            description = "Add {} items to your basket. You will only pay for {} and you will get {} for free".format(
                str(int(x) + int(y)), str(x), str(y))
            return name, description

        if int(y) != 0:
            name = "Buy {} Get {} of the same item at {}% off".format(
                str(x), str(y), str(amount))
            description = "Add {} items to your basket. You will only pay full price for {} and you will get {}% discount for the remaining {} items".format(
                str(int(x) + int(y)), str(x), str(amount), str(y))
            return name, description
        else:
            name = "{}% Discount".format(str(amount))
            description = "{}% Discount at the checkout".format(str(amount))
            return name, description

    def get(self, request, format=None):
        if request.user.is_sales_manager or request.user.is_product_manager:
            item = Campaign.objects.all()
            serializer = CampaignSerializer(item, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request, format=None):
        if request.user.is_sales_manager:
            data = dict(request.data)
            for key in data:
                data[key] = data[key][0]
            name, description = self.name_description(
                data['campaign_x'], data['campaign_y'], data['campaign_amount'])

            data['name'] = name
            data['description'] = description

            serializer = CampaignSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class AdvertisementList(APIView):
    """
    List all advertisements, or create a new advertisement.
    """

    def get(self, request, format=None):
        advertisement = Advertisement.objects.all()
        serializer = AdvertisementSerializer(advertisement, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = AdvertisementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecommendedAdds(APIView):

    @staticmethod
    def get_previous_purchase_categories(user_id):
        orders = Order.objects.filter(buyer=user_id)

        previous_purchase_categories = list()
        for order in orders:
            for item in order.items.all():
                previous_purchase_categories.append(item.category)
        return previous_purchase_categories

    @staticmethod
    def get_random_recommended_advertisement(previous_purchase_categories):
        frequency = {}
        for item in previous_purchase_categories:
            if item in frequency:
                frequency[item] += 1
            else:
                frequency[item] = 1

        counts = frequency.values()
        normalized_counts = [float(i) / sum(counts) for i in counts]
        chosen_category = np.random.choice(
            list(frequency.keys()), p=normalized_counts)

        all_from_chosen_category = Advertisement.objects.filter(
            category__iexact=chosen_category)
        all_from_chosen_category = list(all_from_chosen_category)

        return random.sample(all_from_chosen_category, 1)[0]

    def post(self, request, format=None):

        user_id = request.user.pk

        if len(Order.objects.filter(buyer=user_id)) <= 0:
            return Response({'img': random.sample(list(Advertisement.objects.all()), 1)[0].image})

        previous_purchase_categories = self.get_previous_purchase_categories(
            user_id)

        advertisement = self.get_random_recommended_advertisement(
            previous_purchase_categories)

        data = {'img': advertisement.image}

        return Response(data)
