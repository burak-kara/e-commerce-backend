from rest_framework import serializers
from .models import Item, User, Category


class UserRegistrationSerializer(serializers.ModelSerializer):
    password_validation = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'first_name', 'last_name', 'is_sales_manager',
                  'is_product_manager', 'password', 'password_validation']
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
        )

        password = self.validated_data['password']
        password_validation = self.validated_data['password_validation']

        if password != password_validation:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        user.set_password(password)
        user.save()
        return user


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
                  'campaign',
                  'seller']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']
