import logging
import time

from django.core.cache import cache
from django.db.models import F

from .models import Article

logger = logging.getLogger(__name__)
TRENDING_KEY = "trending_articles"
LOCK_KEY = "trending_articles_lock"


def compute_trending_articles():
    """Deliberately expensive operation used to make cache behavior observable."""
    logger.warning("COMPUTE_TRENDING_ARTICLES")
    time.sleep(2)
    return list(Article.objects.order_by("-view_count", "-published_at").values("id", "title", "view_count")[:5])


def get_trending_articles():
    data = cache.get(TRENDING_KEY)
    if data is not None:
        return data
    if cache.add(LOCK_KEY, "1", timeout=60):
        try:
            data = compute_trending_articles()
            cache.set(TRENDING_KEY, data, timeout=300)
            return data
        finally:
            cache.delete(LOCK_KEY)
    for _ in range(600):
        time.sleep(0.1)
        data = cache.get(TRENDING_KEY)
        if data is not None:
            return data
    raise TimeoutError("Timed out waiting for trending cache regeneration")


def get_trending_articles_unsafe():
    """Phase-2 checkpoint only: get_or_set does not protect the callable."""
    return cache.get_or_set(TRENDING_KEY, compute_trending_articles, timeout=300)


def increment_all_view_counts():
    Article.objects.update(view_count=F("view_count") + 1)
    cache.delete(TRENDING_KEY)
