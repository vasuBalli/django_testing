from django.urls import path
from . import views

urlpatterns = [
    path("info/", views.info),
    path("testing/", views.testing),
    path("download/", views.download),
    path("health/", views.health), #4
]
