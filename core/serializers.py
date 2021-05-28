from rest_framework import serializers
from .models import Item, User, Category, Order, Review, Campaign, Advertisement
from django.conf import settings
import uuid
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
import json

private_key_master = settings.PRIVATE_KEY
public_key_master = '0xB78DFDdF8af06485b5358ad98950119F6f270AE4'

contract_address = '0x1781684a1A5eff097C631E227d654a3470842e45'


def initialize_chain_connection():
    w3 = Web3(Web3.HTTPProvider(
        "https://data-seed-prebsc-2-s1.binance.org:8545/"))  # "1-s2 provider has the most uptime" - Emir
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)  # might cause errors lul
    return w3


def create_wallet():
    w3 = initialize_chain_connection()
    created_wallet_address = w3.eth.account.create()
    return created_wallet_address.address, created_wallet_address.privateKey.hex()


def transferBNB(target_acc):
    signed_txn = w3.eth.account.signTransaction(dict(
        nonce=w3.eth.getTransactionCount(public_key_master),
        to=target_acc,
        gasPrice=w3.eth.gasPrice,
        gas=100000,
        value=w3.toWei(0.005, 'ether'),
        data='',
    ),
        private_key_master, )
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    txn_id = w3.eth.waitForTransactionReceipt(txn_hash)['transactionHash']
    return txn_id


w3 = initialize_chain_connection()
contract_abi_directory = './static/blockchain/contract_abi.json'
f = open(contract_abi_directory)
temp_abi = json.load(f)
contract = w3.eth.contract(address=contract_address, abi=temp_abi)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password_validation = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'first_name', 'last_name', 'is_sales_manager',
                  'is_product_manager', 'password', 'password_validation']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    public_key, private_key = create_wallet()
    wallet_address = public_key
    private_wallet_address = private_key
    transferBNB(wallet_address)

    def save(self, request):
        user = User(
            username=self.validated_data['username'],
            email=self.validated_data['email'],
            phone_number=self.validated_data['phone_number'],
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            is_sales_manager=self.validated_data['is_sales_manager'],
            is_product_manager=self.validated_data['is_product_manager'],
            wallet_address=self.wallet_address,
            private_wallet_address=self.private_wallet_address
        )

        password = self.validated_data['password']
        password_validation = self.validated_data['password_validation']

        if password != password_validation:
            raise serializers.ValidationError(
                {'password': 'Passwords must match.'})
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email',
                  'phone_number',
                  'first_name',
                  'last_name',
                  'addresses',
                  'is_sales_manager',
                  'is_product_manager',
                  'is_admin',
                  'twoFA_enabled',
                  'balance',
                  'wallet_address',
                  ]


class UserSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk',
                  'username',
                  'first_name',
                  'last_name',  
                  'is_sales_manager',
                  'is_product_manager',
                  ]


class UserPrivilegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk',
                  'username',
                  'is_sales_manager',
                  'is_product_manager',
                  ]


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username',
                  'first_name',
                  'last_name',
                  'balance',
                  'wallet_address',
                  ]


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id',
                  'name',
                  'brand',
                  'category',
                  'price',
                  'stock',
                  'image',
                  'description',
                  'specs',
                  'mean_rating',
                  'review_count',
                  'campaign',
                  'seller']

class ItemPriceFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id',
                  'name',
                  'brand',
                  'category',
                  'price',
                  'stock',
                  'image',
                  'description',
                  'specs',
                  'mean_rating',
                  'review_count',
                  'campaign',
                  'seller']

class ItemPriceRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id',
                  'name',
                  'brand',
                  'category',
                  'price',
                  'stock',
                  'image',
                  'description',
                  'specs',
                  'mean_rating',
                  'review_count',
                  'campaign',
                  'seller']



class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id',
                  'buyer',
                  'items',
                  'item_counts',
                  'total_price',
                  'date',
                  'delivery_address',
                  'status']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id',
                  'date',
                  'comment',
                  'rating',
                  'title',
                  'user',
                  'item',
                  'status']


# Campaign


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = ['id',
                  'valid_until',
                  'campaign_x',
                  'campaign_y',
                  'campaign_amount']


class AdvertisementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertisement
        fields = ['category', 'image']
