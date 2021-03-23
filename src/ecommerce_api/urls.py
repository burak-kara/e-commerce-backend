from django.contrib import admin
from django.urls import path, include

from core.views import ItemView

urlpatterns = [
    path('api-auth/', include('rest_framework.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('', admin.site.urls),
    path('api/items', ItemView.as_view(), name='item'),
]
