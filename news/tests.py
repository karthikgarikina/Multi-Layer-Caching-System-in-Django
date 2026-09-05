from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from .models import Article
from .services import LOCK_KEY, TRENDING_KEY, get_trending_articles


class CacheContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("reader", password="password")
        cls.article = Article.objects.create(title="A", body="Old body", author=cls.user, category="News", view_count=1)

    def setUp(self):
        cache.clear()

    def test_list_varies_on_cookie_and_is_cached_for_900_seconds(self):
        response = self.client.get("/articles/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Cookie", response["Vary"])
        self.assertIn("max-age=900", response["Cache-Control"])
        self.assertContains(response, "Welcome, anonymous")
        self.client.login(username="reader", password="password")
        self.assertContains(self.client.get("/articles/"), "Welcome, reader")

    def test_save_invalidates_trending(self):
        cache.set(TRENDING_KEY, ["cached"], 300)
        self.article.title = "Changed"
        self.article.save()
        self.assertIsNone(cache.get(TRENDING_KEY))

    def test_trending_endpoint_caches_its_low_level_result(self):
        with patch("news.services.compute_trending_articles", return_value=[]) as compute:
            self.assertEqual(self.client.get("/articles/trending/").status_code, 200)
            self.assertEqual(self.client.get("/articles/trending/").status_code, 200)
        self.assertEqual(compute.call_count, 1)
        self.assertEqual(cache.get(TRENDING_KEY), [])

    def test_bulk_endpoint_invalidates_trending(self):
        cache.set(TRENDING_KEY, ["cached"], 300)
        self.assertEqual(self.client.post("/articles/bulk-view-increment/").status_code, 204)
        self.assertIsNone(cache.get(TRENDING_KEY))

    def test_fragment_key_changes_after_save(self):
        first = self.client.get(f"/articles/{self.article.pk}/")["X-Fragment-Cache-Key"]
        self.article.body = "New body"
        self.article.save()
        second = self.client.get(f"/articles/{self.article.pk}/")["X-Fragment-Cache-Key"]
        self.assertNotEqual(first, second)

    def test_lock_allows_one_compute(self):
        with patch("news.services.compute_trending_articles", return_value=[]) as compute:
            with ThreadPoolExecutor(max_workers=10) as pool:
                list(pool.map(lambda _: get_trending_articles(), range(10)))
        self.assertEqual(compute.call_count, 1)
        self.assertIsNone(cache.get(LOCK_KEY))
