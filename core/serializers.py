from rest_framework import serializers
from .models import Item, User, Category, Order, Review

class UserRegistrationSerializer(serializers.ModelSerializer):
    password_validation = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'first_name', 'last_name', 'is_sales_manager',
                  'is_product_manager', 'password', 'password_validation', 'wallet_address','private_wallet_address']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def save(self, request):
        user = User(
            username=self.validated_data['username'],
            email=self.validated_data['email'],
            phone_number=self.validated_data['phone_number'],
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            is_sales_manager=self.validated_data['is_sales_manager'],
            is_product_manager=self.validated_data['is_product_manager'],
            wallet_address=self.validated_data['wallet_address'],
            private_wallet_address=self.validated_data['private_wallet_address']
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
                  'private_wallet_address']

class UserSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 
                  'first_name', 
                  'last_name', 
                  'is_sales_manager',
                  'is_product_manager', 
                  'is_admin',
                  'is_superuser'
                  ]
                  
class UserSalesMgrSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ['username',
              'first_name', 
              'last_name', 
              'is_sales_manager',
              ]
              
class UserProductMgrSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ['username', 
              'first_name', 
              'last_name', 
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
                  'private_wallet_address']


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
