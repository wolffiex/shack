from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.templatetags.static import static
from django.db.models import Q, JSONField, UniqueConstraint


class Animation(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    file_path = models.FilePathField(path="render", null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    served_at = models.DateTimeField(null=True, blank=True, default=None)

    class Source(models.TextChoices):
        STATIC = "static"
        RAYS = "rays"
        SPOTIFY = "spotify"

    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.STATIC
    )
    metadata = JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=["start_time"])]
        constraints = [
            UniqueConstraint(
                fields=["start_time"],
                condition=Q(start_time__isnull=False),
                name="unique_start_time_if_not_null",
            )
        ]

    @property
    def start_time_local(self):
        return self.start_time.astimezone(timezone.get_current_timezone())

    def clean(self):
        super().clean()
        if self.start_time:
            if self.start_time.microsecond != 0:
                raise ValidationError("Start time milliseconds must be zero.")
            if self.start_time.second not in [0, 15, 30, 45]:
                raise ValidationError(
                    "Start time seconds must be one of 0, 15, 30, or 45."
                )

    def save(self, *args, **kwargs):
        self.full_clean()  # Validate the model before saving
        super().save(*args, **kwargs)

    @classmethod
    def get_next_animation(cls, current_time: datetime):
        return (
            cls.objects.filter(
                Q(start_time__isnull=True, served_at__isnull=True)
                | Q(start_time__gt=current_time)
            )
            .order_by("start_time", "created_at")
            .first()
        )

    @staticmethod
    def align_time(t: datetime) -> datetime:
        second = t.second
        if 0 <= second < 15:
            next_second = 15
        elif 15 <= second < 30:
            next_second = 30
        elif 30 <= second < 45:
            next_second = 45
        else:
            next_second = 0
            t += timedelta(minutes=1)

        return t.replace(second=next_second, microsecond=0, tzinfo=t.tzinfo)

    @property
    def url(self):
        return (
            "/pushbyt/" + self.file_path if self.file_path else static("missing.webp")
        )


class Lock(models.Model):
    name = models.CharField(max_length=100, unique=True)
    acquired = models.BooleanField(default=False)
