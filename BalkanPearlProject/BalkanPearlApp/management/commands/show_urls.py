from django.core.management.base import BaseCommand
from django.urls import get_resolver

class Command(BaseCommand):
    help = "Показать все URL-адреса проекта"

    def handle(self, *args, **options):
        resolver = get_resolver()
        self.print_urls(resolver.url_patterns)

    def print_urls(self, patterns, parent_pattern=''):
        for pattern in patterns:
            if hasattr(pattern, 'url_patterns'):
                # Для include()
                self.print_urls(
                    pattern.url_patterns,
                    parent_pattern + str(pattern.pattern)
                )
            else:
                # Для прямых URL
                full_path = parent_pattern + str(pattern.pattern)
                self.stdout.write(
                    f"{full_path.ljust(60)} | {pattern.name or '—'}"
                )