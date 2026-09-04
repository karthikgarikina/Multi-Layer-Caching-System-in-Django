from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from news.models import Article


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        admin, _ = User.objects.get_or_create(username="admin", defaults={"is_staff": True, "is_superuser": True})
        admin.set_password("admin")
        admin.save()
        reporter, _ = User.objects.get_or_create(username="reporter")
        reporter.set_password("reporter")
        reporter.save()
        for number in range(1, 11):
            Article.objects.get_or_create(title=f"Seed article {number}", defaults={"body": f"Body for seed article {number}.", "author": admin if number % 2 else reporter, "category": "General", "view_count": number})
        self.stdout.write("News seed data ready")
