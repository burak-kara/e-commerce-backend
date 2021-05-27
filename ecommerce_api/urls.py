from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_auth.registration.views import VerifyEmailView, RegisterView
from allauth.account.views import confirm_email
from django.urls import re_path

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
    # Review URLs
    path('api/reviews/', views.ReviewList.as_view()),
    path('api/reviews/<int:pk>/', views.ReviewDetail.as_view()),
    path('api/item/reviews/<int:item>/', views.ReviewsOfItem.as_view()),
    path('api/rating-from-comment/', views.RetrieveRatingFromComment.as_view()),
    path('api/get-recomended-products/<int:recommendation_count>/',
         views.RecommendedProducts.as_view()),
    # Verify Email URLs
    path('rest-auth/registration/', RegisterView.as_view(), name='account_signup'),
    url(r'^verify-email/$', VerifyEmailView.as_view(),
        name='account_email_verification_sent'),
    path('rest-auth/registration/account-confirm-email/<key>',
         confirm_email, name='account_confirm_email'),
    # 2fa URLs
    re_path(r'^totp/create/$', views.TOTPCreateView.as_view(), name='totp-create'),
    re_path(r'^totp/login/(?P<token>[0-9]{6})/$',
            views.TOTPVerifyView.as_view(), name='totp-login'),
    #funding URL
    path('api/funding/', views.Funding.as_view()),
    path('api/funding/<int:amount>/', views.Funding.as_view()),
    # get all users
    path('api/getAll/', views.GetAllUsers.as_view()),
    path('api/updateSales/', views.updateUserSalesMgr.as_view()),
    path('api/updateProduct/', views.updateUserProductMgr.as_view()),
    
    # Statistics
    path('api/stats/', views.StatisticDetail.as_view()),

    # Campaign
    path('api/campaign/<str:uuid>/', views.CampaignDetail.as_view()),
    path('api/campaign/', views.CampaignList.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)
