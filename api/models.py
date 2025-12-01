from django.db import models

class TrafficLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    path = models.CharField(max_length=512, db_index=True)
    method = models.CharField(max_length=10)
    status_code = models.PositiveSmallIntegerField(null=True, db_index=True)
    response_time_ms = models.FloatField(null=True, db_index=True)
    user_agent = models.TextField(blank=True)
    referer = models.CharField(max_length=1024, blank=True)
    content_length = models.BigIntegerField(null=True, blank=True)
    is_ajax = models.BooleanField(default=False)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["path", "timestamp"]),
            models.Index(fields=["status_code"]),
        ]

    def __str__(self):
        return f"{self.timestamp} {self.ip} {self.method} {self.path} {self.status_code}"
    

class NginxTraffic(models.Model):
    timestamp = models.DateTimeField(db_index=True)
    ip = models.GenericIPAddressField(db_index=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=512, db_index=True)
    status_code = models.PositiveSmallIntegerField()
    bytes_sent = models.BigIntegerField(null=True)
    user_agent = models.TextField(blank=True)
    referer = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['ip']),
            models.Index(fields=['path']),
        ]

