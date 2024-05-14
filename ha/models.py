from django.db import models
from django.utils import timezone


class Timer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField()
    canceled = models.BooleanField(default=False)

    @property
    def is_running(self) -> bool:
        if not self.canceled:
            expiration_time = self.created_at + self.duration
            return expiration_time > timezone.now()
        return False

    @property
    def timestamp(self) -> int:
        expiration_time = self.created_at + self.duration
        return round(expiration_time.timestamp())
