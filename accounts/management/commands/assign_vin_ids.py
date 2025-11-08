"""
Management command to assign VIN IDs to existing users who don't have one.
Run: python manage.py assign_vin_ids
"""
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from django.db.models import Max


class Command(BaseCommand):
    help = 'Assign VIN IDs to existing users who don\'t have one'

    def handle(self, *args, **options):
        # Get users without VIN IDs
        users_without_vin = CustomUser.objects.filter(vin_id__isnull=True) | CustomUser.objects.filter(vin_id='')
        
        if not users_without_vin.exists():
            self.stdout.write(self.style.SUCCESS('All users already have VIN IDs!'))
            return
        
        # Get all existing VIN IDs and find the highest number
        existing_vins = CustomUser.objects.exclude(
            vin_id__isnull=True
        ).exclude(
            vin_id=''
        ).values_list('vin_id', flat=True)
        
        max_number = 0
        for vin in existing_vins:
            try:
                number = int(vin.split('-')[1])
                max_number = max(max_number, number)
            except (IndexError, ValueError):
                continue
        
        next_number = max_number + 1
        
        # Assign VIN IDs to users without one
        count = 0
        for user in users_without_vin:
            user.vin_id = f"VIN-{next_number:07d}"
            user.save()
            self.stdout.write(f'Assigned {user.vin_id} to {user.username}')
            next_number += 1
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully assigned VIN IDs to {count} user(s)!'))

