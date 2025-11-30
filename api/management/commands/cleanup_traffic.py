from django.core.management.base import BaseCommand
from api.models import TrafficLog
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = "Delete traffic logs older than N days (default 30 days)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)
        qs = TrafficLog.objects.filter(timestamp__lt=cutoff)
        count = qs.count()
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} logs older than {days} days."))
