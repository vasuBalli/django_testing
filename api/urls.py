from django.urls import path
from . import views

urlpatterns = [
    path("api/info/", views.info),
    path("api/download/", views.download),
    path("api/health/", views.health),
]
