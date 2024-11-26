from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'crawler', views.CrawlerViewSet, basename='crawler')

urlpatterns = [
    path('search/', views.search, name='search'),
    path('validate/', views.validate_address, name='validate'),
    path('api/', include(router.urls)),
]
