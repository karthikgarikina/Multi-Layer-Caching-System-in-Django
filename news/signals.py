from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Article
from .services import TRENDING_KEY


@receiver(post_save, sender=Article)
def invalidate_trending_articles(sender, **kwargs):
    cache.delete(TRENDING_KEY)
