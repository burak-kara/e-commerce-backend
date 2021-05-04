from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.urlpatterns import format_suffix_patterns
from rest_auth.registration.views import VerifyEmailView, RegisterView
#from two_factor.urls import urlpatterns as tf_urls

from core import views

urlpatterns = [
    #path('', include(tf_urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('', admin.site.urls),
    path('api/categories/', views.CategoryList.as_view()),
    path('api/brands/<category>/', views.BrandList.as_view()),
    path('api/items/', views.ItemList.as_view()),
    path('api/items/search', views.ItemSearch.as_view()),
    path('api/items/<int:pk>/', views.ItemDetail.as_view()),
    path('api/items/<category>/', views.ItemsByCategory.as_view()),
    path('api/user/', views.UserDetail.as_view()),
    path('api/orders/', views.OrderList.as_view()),
    path('api/orders/<int:pk>/', views.OrderDetail.as_view()),
    path('api/addresses/<int:pk>/', views.AddressDetail.as_view()),
    # Review links
    path('api/reviews/', views.ReviewList.as_view()),
    path('api/reviews/<int:pk>/', views.ReviewDetail.as_view()),
    path('api/item/reviews/<int:item>/', views.ReviewsOfItem.as_view()),
    # Verify Email Views
    path('rest-auth/registration/', RegisterView.as_view(), name='account_signup'),
    re_path(r'^account-confirm-email/', VerifyEmailView.as_view(),
            name='account_email_verification_sent'),
    re_path(r'^account-confirm-email/(?P<key>[-:\w]+)/$', VerifyEmailView.as_view(),
            name='account_confirm_email'),


]

urlpatterns = format_suffix_patterns(urlpatterns)
