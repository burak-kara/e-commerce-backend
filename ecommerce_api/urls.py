from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_auth.registration.views import VerifyEmailView, RegisterView
from django.views.generic import TemplateView
from allauth.account.views import confirm_email
# from two_factor.urls import urlpatterns as tf_urls

from core import views

urlpatterns = [
    # path('', include(tf_urls)),
    path('', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('api/orders/', views.OrderList.as_view()),
    path('rest-auth/registration/', include('rest_auth.registration.urls')),

    path('api/categories/', views.CategoryList.as_view()),
    path('api/brands/<category>/', views.BrandList.as_view()),
    path('api/items/', views.ItemList.as_view()),
    path('api/items/search', views.ItemSearch.as_view()),
    path('api/items/<int:pk>/', views.ItemDetail.as_view()),
    path('api/items/<category>/', views.ItemsByCategory.as_view()),
    path('api/user/', views.UserDetail.as_view()),

    path('api/orders/<int:pk>/', views.OrderDetail.as_view()),
    path('api/addresses/<int:pk>/', views.AddressDetail.as_view()),
    # Review links
    path('api/reviews/', views.ReviewList.as_view()),
    path('api/reviews/<int:pk>/', views.ReviewDetail.as_view()),
    path('api/item/reviews/<int:item>/', views.ReviewsOfItem.as_view()),
    # Verify Email Views
    path('rest-auth/registration/', RegisterView.as_view(), name='account_signup'),
    url(r'^verify-email/$', VerifyEmailView.as_view(),
        name='account_email_verification_sent'),
    path('rest-auth/registration/account-confirm-email/<key>',
         confirm_email, name='account_confirm_email')


]

urlpatterns = format_suffix_patterns(urlpatterns)
