from concurrent.futures import ThreadPoolExecutor

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.test.utils import override_settings

from news import services


class Command(BaseCommand):
    help = "Demonstrate unsafe get_or_set or verify the Redis-lock implementation."

    def add_arguments(self, parser):
        parser.add_argument("--unsafe", action="store_true")
        parser.add_argument("--workers", type=int, default=10)

    def handle(self, *args, **options):
        cache.delete_many([services.TRENDING_KEY, services.LOCK_KEY])
        calls = 0
        original = services.compute_trending_articles

        def counted():
            nonlocal calls
            calls += 1
            return original()

        services.compute_trending_articles = counted
        try:
            getter = services.get_trending_articles_unsafe if options["unsafe"] else services.get_trending_articles
            with ThreadPoolExecutor(max_workers=options["workers"]) as pool:
                list(pool.map(lambda _: getter(), range(options["workers"])))
        finally:
            services.compute_trending_articles = original
        mode = "unsafe get_or_set" if options["unsafe"] else "distributed lock"
        self.stdout.write(f"{mode}: compute_trending_articles executed {calls} time(s)")
