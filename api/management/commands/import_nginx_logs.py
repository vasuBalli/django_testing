import re
from datetime import datetime
from django.core.management.base import BaseCommand
from downloader.models import NginxTraffic

LOG_FILE = "/var/log/nginx/access.log"

# Nginx default combined format
LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) - - \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" '
    r'(?P<status>\d{3}) (?P<bytes>\S+) '
    r'"(?P<referer>[^"]*)" "(?P<agent>[^"]*)"'
)

class Command(BaseCommand):
    help = "Import nginx access log into Django database"

    def handle(self, *args, **kwargs):
        count = 0
        with open(LOG_FILE, "r") as f:
            for line in f:
                match = LOG_PATTERN.match(line)
                if not match:
                    continue

                d = match.groupdict()

                # Parse timestamp like: 01/Dec/2025:12:34:56 +0000
                timestamp = datetime.strptime(
                    d["time"].split()[0],
                    "%d/%b/%Y:%H:%M:%S"
                )

                NginxTraffic.objects.create(
                    timestamp=timestamp,
                    ip=d["ip"],
                    method=d["method"],
                    path=d["path"],
                    status_code=int(d["status"]),
                    bytes_sent=int(d["bytes"]) if d["bytes"].isdigit() else 0,
                    user_agent=d["agent"],
                    referer=d["referer"],
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {count} logs"))
