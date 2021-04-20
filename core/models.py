from django.db import models
from django.core import validators
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, phone_number, first_name, last_name, is_sales_manager, is_product_manager,
                    password=None):
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            is_sales_manager=is_sales_manager,
            is_product_manager=is_product_manager
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, phone_number, first_name, last_name, password=None):
        user = self.create_user(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            is_sales_manager=True,
            is_product_manager=True
        )

        user.is_staff = True
        user.is_admin = True
        user.is_superuser = True
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(verbose_name='email', max_length=60, unique=True)
    phone_number = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(verbose_name='first_name', max_length=30)
    last_name = models.CharField(verbose_name='last_name', max_length=30)
    wallet_address = models.CharField(max_length=400)
    date_joined = models.DateField(verbose_name='date joined', auto_now_add=True)
    last_login = models.DateField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_product_manager = models.BooleanField(default=False)
    is_sales_manager = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = ['email', 'phone_number', 'first_name', 'last_name', ]

    objects = CustomUserManager()

    def __str__(self):
        return self.first_name + ' - ' + self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True


class Item(models.Model):
    name = models.CharField(max_length=200, default='')
    brand = models.CharField(max_length=100, default='Other')
    category = models.CharField(max_length=100, default='Other')
    price = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    image = models.CharField(max_length=1000, default='#')
    description = models.CharField(max_length=1000, blank=True, default='')
    specs = models.CharField(max_length=1000, blank=True, default='')
    campaign = models.CharField(max_length=200, blank=True, default='')
    seller = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=200, default='')

    def __str__(self):
        return self.name


class Order(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Item)
    item_counts = models.CharField(max_length=600, validators=[validators.int_list_validator()])
    total_price = models.IntegerField(default=0)
    date = models.DateField(verbose_name='order_date', auto_now_add=True)
    delivery_address = models.CharField(max_length=1000, default='Self Pick Up')

    WAITING_FOR_PAYMENT = 0
    PAYMENT_CONFIRMED = 1
    APPROVED = 2
    PREPARING = 3
    SHIPPED = 4
    DELIVERED = 5
    REJECTED = 6
    STATUS_CHOICES = (
        (WAITING_FOR_PAYMENT, 'Waiting For Payment'),
        (PAYMENT_CONFIRMED, 'Payment Confirmed'),
        (APPROVED, 'Approved'),
        (PREPARING, 'Preparing'),
        (SHIPPED, 'Shipped'),
        (DELIVERED, 'Delivered'),
        (REJECTED, 'Rejected')
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=WAITING_FOR_PAYMENT)

    def __str__(self):
        return str(self.buyer) + str(self.items)
