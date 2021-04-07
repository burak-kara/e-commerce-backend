from django.contrib import admin
from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

from core.views import ItemList, CategoryList, ItemDetail

urlpatterns = [
    path('api-auth/', include('rest_framework.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('', admin.site.urls),
    path('api/categories/', CategoryList.as_view()),
    path('api/items/', ItemList.as_view()),
    path('api/items/<int:pk>/', ItemDetail.as_view()),
    path('api/items/<category>/', ItemDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
