from django.contrib import admin
from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

from core import views

urlpatterns = [
    path('api-auth/', include('rest_framework.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('', admin.site.urls),
    path('api/categories/', views.CategoryList.as_view()),
    path('api/items/', views.ItemList.as_view()),
    path('api/items/<int:pk>/', views.ItemDetail.as_view()),
    path('api/items/<category>/', views.ItemsByCategory.as_view()),
    path('api/user/', views.UserDetail.as_view()),
    path('api/orders/', views.OrderList.as_view()),
    path('api/orders/<int:pk>/', views.OrderDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
