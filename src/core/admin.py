from django.contrib import admin
from .models import Item, User, Category
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site


class AccountAdmin(UserAdmin):
    list_display = (
        'pk', 'username', 'email', 'phone_number', 'first_name', 'last_name', 'is_sales_manager', 'is_product_manager',
        'is_superuser')
    search_fields = ('pk', 'username', 'email')
    readonly_fields = ('pk', 'date_joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(User, AccountAdmin)
admin.site.register(Item)
admin.site.register(Category)

admin.site.unregister(Group)
admin.site.unregister(Site)
