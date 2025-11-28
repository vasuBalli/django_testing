from django.urls import path
from .views import info, download

urlpatterns = [
    path("info/", info),
    path("download/", download),
]
