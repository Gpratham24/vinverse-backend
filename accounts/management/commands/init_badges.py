"""
Management command to initialize badges in the database.
Run: python manage.py init_badges
"""
from django.core.management.base import BaseCommand
from accounts.models import Badge
from accounts.badges import BADGES


class Command(BaseCommand):
    help = 'Initialize badges in the database'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        
        for badge_key, badge_data in BADGES.items():
            badge, created = Badge.objects.update_or_create(
                key=badge_key,
                defaults={
                    'name': badge_data['name'],
                    'description': badge_data['description'],
                    'icon': badge_data['icon'],
                    'color': badge_data['color'],
                    'badge_type': 'streak' if 'streak' in badge_key else 'achievement',
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created badge: {badge.icon} {badge.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated badge: {badge.icon} {badge.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully initialized badges! '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )

