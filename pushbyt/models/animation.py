from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.templatetags.static import static
from django.db.models import Q, JSONField, UniqueConstraint, F
import logging

logger = logging.getLogger(__name__)
NINETY_SECONDS = timedelta(seconds=90)


class Animation(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    file_path = models.FilePathField(path="render", null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    served_at = models.DateTimeField(null=True, blank=True, default=None)

    class Source(models.TextChoices):
        STATIC = "static"
        RAYS = "rays"
        SPOTIFY = "spotify"
        TIMER = "timer"
        DOORBELL = "doorbell"
        RADAR = "radar"

    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.STATIC
    )
    metadata = JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["start_time"])]
        constraints = [
            UniqueConstraint(
                fields=["start_time", "source"],
                condition=Q(start_time__isnull=False),
                name="unique_start_time_source_if_not_null",
            )
        ]

    def clean(self):
        super().clean()
        if self.start_time:
            if self.start_time.microsecond != 0:
                raise ValidationError("Start time milliseconds must be zero.")
            if self.start_time.second not in [0, 12, 24, 36, 48]:
                raise ValidationError(
                    "Start time seconds must be one of 0, 12, 24, 36, or 48."
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
            .order_by(F("start_time").asc(nulls_first=True), "created_at")
            .first()
        )

    @staticmethod
    def align_time(t: datetime) -> datetime:
        """
        Align a datetime to the nearest 12-second boundary (0, 12, 24, 36, 48).

        This aligns with the device polling interval of ~12 seconds, ensuring
        smooth animation transitions.
        """
        seconds = [0, 12, 24, 36, 48]
        s = 0
        while (t.second + s) % 60 not in seconds:
            s += 1

        return t.replace(microsecond=0, tzinfo=t.tzinfo) + timedelta(seconds=s)

    @staticmethod
    def next_time(t: datetime) -> datetime:
        return Animation.align_time(t)

    @property
    def url(self):
        return (
            "/pushbyt/" + self.file_path if self.file_path else static("missing.webp")
        )
