from django.db import models
from .api_token import ApiToken
from .animation import Animation
import logging

logger = logging.getLogger(__name__)


class Lock(models.Model):
    name = models.CharField(max_length=100, unique=True)
    acquired = models.BooleanField(default=False)

__all__ =["ApiToken", "Animation", "Lock"]
