from django.db import models
from django.utils import timezone


class Timer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField()
    canceled = models.BooleanField(default=False)

    @classmethod
    def get_last_timer(cls):
        now = timezone.now()
        timer = cls.objects.annotate(
            expiration_time=models.ExpressionWrapper(
                models.F('created_at') + models.F('duration'),
                output_field=models.DateTimeField()
            )
        ).filter(
            expiration_time__gt=now,
        ).order_by('-created_at').first()

        return timer if timer and not timer.canceled else None
