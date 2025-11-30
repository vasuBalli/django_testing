from django.urls import path
from . import views

urlpatterns = [
    path("info/", views.info),
    path("testing/", views.testing),
    path("download/", views.download),
    path("health/", views.health), #4
    path("admin/traffic/", views.admin_traffic_dashboard, name="admin_traffic_dashboard"),
    path("admin/traffic/data/", views.admin_traffic_data, name="admin_traffic_data"),
]
