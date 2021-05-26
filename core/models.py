from django.db import models
from django.core import validators
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
import uuid

private_key_master = '95b3eb7b43f5352ad277b7260438ed8f13ab14deaa9c5eee77352cea1a4ce0d6'
public_key_master = ''

contract_address = '0x1781684a1A5eff097C631E227d654a3470842e45'

def initialize_chain_connection():
    w3 = Web3(Web3.HTTPProvider("https://data-seed-prebsc-2-s1.binance.org:8545/")) # "1-s2 provider has the most uptime" - Emir
    w3.middleware_onion.inject(geth_poa_middleware, layer=0) # might cause errors lul 
    return w3

w3 = initialize_chain_connection()
contract_abi_directory = 'D:/Agile/development/static/blockchain/contract_abi.json'
f = open(contract_abi_directory)
temp_abi = json.load(f)
contract = w3.eth.contract(address =contract_address , abi =temp_abi)

# print("ABC")




class CustomUserManager(BaseUserManager):

    # def initialize_chain_connection():
    #         w3 = Web3(Web3.HTTPProvider("https://data-seed-prebsc-2-s1.binance.org:8545/")) # "1-s2 provider has the most uptime" - Emir
    #         w3.middleware_onion.inject(geth_poa_middleware, layer=0) # might cause errors lul 
    #         return w3

    # def create_wallet(self):
    #     w3 = initialize_chain_connection()
    #     created_wallet_address = w3.eth.account.create()
    #     print(created_wallet_address.address)
    #     print(created_wallet_address.privateKey)
    #     return created_wallet_address.address, created_wallet_address.privateKey.hex()

    def create_user(self, username, email, phone_number, first_name, last_name, is_sales_manager, is_product_manager,private_wallet_address=None,wallet_address=None,password=None):
        a,b = self.create_wallet()    
        wallet_address = a
        private_wallet_address = b
        print(wallet_address)
        print(private_wallet_address)
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            is_sales_manager=is_sales_manager,
            is_product_manager=is_product_manager,
            wallet_address = wallet_address,
            private_wallet_address= private_wallet_address
            )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, phone_number, first_name, last_name, password=None):
        a,b = self.create_wallet() # a is wallet address , b is private key
        wallet_address = a
        private_wallet_address = b
        print(wallet_address)
        print(private_wallet_address)
        user = self.create_user(
            username=username,
            email=self.normalize_email(email),
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            is_sales_manager=True,
            is_product_manager=True,
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
    addresses = models.CharField(max_length=1200, blank=True)
    date_joined = models.DateField(
        verbose_name='date joined', auto_now_add=True)
    last_login = models.DateField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_product_manager = models.BooleanField(default=False)
    is_sales_manager = models.BooleanField(default=False)
    twoFA_enabled = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=11, decimal_places=5, default=0.0)
    wallet_address = models.CharField(max_length=200)
    private_wallet_address = models.CharField(max_length=200)


    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = ['email', 'phone_number', 'first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.first_name + ' - ' + self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

# Campaign


class Campaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    valid_until = models.DateTimeField()
    campaign_x = models.IntegerField(default=1)
    campaign_y = models.IntegerField(default=0)
    campaign_amount = models.IntegerField(default=0)

    def __str__(self):
        return "campaign_buy_" + str(self.campaign_x) + "_get_"+str(self.campaign_y) + "_"+str(self.campaign_amount)


class Item(models.Model):
    name = models.CharField(max_length=200, default='')
    brand = models.CharField(max_length=100, default='Other')
    category = models.CharField(max_length=100, default='Other')
    price = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    image = models.CharField(max_length=1000, default='#')
    description = models.CharField(max_length=1000, blank=True, default='')
    specs = models.CharField(max_length=1000, blank=True, default='')
    mean_rating = models.IntegerField(default=None,
                                      validators=[validators.MaxValueValidator(5), validators.MinValueValidator(0)])
    review_count = models.IntegerField(default=0)
    campaign = models.ManyToManyField(Campaign, blank=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, default=2)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=200, default='')

    def __str__(self):
        return self.name


class Order(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Item)
    item_counts = models.CharField(max_length=600, validators=[
                                   validators.int_list_validator()])
    total_price = models.FloatField(default=0.0)
    date = models.DateField(verbose_name='order_date', auto_now_add=True)
    delivery_address = models.CharField(
        max_length=1000, default='Self Pick Up')

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
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=WAITING_FOR_PAYMENT)

    def __str__(self):
        return str(self.buyer) + str(self.items)


class Review(models.Model):
    date = models.DateTimeField(auto_now=True)
    comment = models.TextField(default='')
    rating = models.IntegerField(default=0,
                                 validators=[validators.MaxValueValidator(5), validators.MinValueValidator(0)])
    title = models.CharField(max_length=100, default='', blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=False)

    WAITING_FOR_APPROVAL = 0
    APPROVED = 1
    REJECTED = 2
    STATUS_CHOICES = (
        (WAITING_FOR_APPROVAL, 'Waiting For Approval'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected')
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=WAITING_FOR_APPROVAL)

    def __str__(self):
        return "rev_id_" + str(self.id)
