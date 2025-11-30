from django.contrib import admin
from .models import TrafficLog

@admin.register(TrafficLog)
class TrafficLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "ip", "method", "path", "status_code", "response_time_ms", "content_length")
    list_filter = ("status_code", "method", "is_ajax")
    search_fields = ("ip", "path", "user_agent", "referer")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)
    list_per_page = 50
