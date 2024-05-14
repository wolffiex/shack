from django.db import models
from django.db.models import F, ExpressionWrapper, Q, Func, DateTimeField
from django.utils import timezone
from datetime import timedelta


class Timer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    minutes = models.IntegerField()
    canceled = models.BooleanField(default=False)

    @classmethod
    def get_last_unexpired_timer(cls):
        now = timezone.now()
        expiration_time = ExpressionWrapper(
            F('created_at') + Func(F('minutes'), function='make_interval',
                                   args=['0:0:0:0:0', '0:0:0', 'minutes']),
            output_field=DateTimeField()
        )
        return cls.objects.annotate(expiration_time=expiration_time).filter(
            Q(expiration_time__gt=now) & Q(canceled=False)
        ).order_by('-created_at').first()
