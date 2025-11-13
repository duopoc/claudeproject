"""
Management command to complete superuser profile setup
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Complete superuser profile setup'

    def handle(self, *args, **kwargs):
        self.stdout.write('\n=== Complete Superuser Profile Setup ===\n')
        
        # Get all superusers with incomplete profiles
        superusers = User.objects.filter(is_superuser=True)
        
        for user in superusers:
            profile = user.profile
            
            # Check if profile is incomplete
            if not profile.firstname or not profile.lastname:
                self.stdout.write(f'\nSetting up profile for superuser: {user.username}')
                
                firstname = input('First name (ชื่อ): ').strip()
                lastname = input('Last name (นามสกุล): ').strip()
                
                gender_choice = input('Gender (1=Male/ชาย, 2=Female/หญิง) [1]: ').strip() or '1'
                gender = 'male' if gender_choice == '1' else 'female'
                
                age = input('Age (อายุ) [30]: ').strip() or '30'
                try:
                    age = int(age)
                except ValueError:
                    age = 30
                
                phone = input('Phone (เบอร์โทรศัพท์): ').strip() or '000-000-0000'
                
                # Update profile
                profile.firstname = firstname
                profile.lastname = lastname
                profile.gender = gender
                profile.age = age
                profile.phone = phone
                profile.role = 'superuser'
                profile.is_active_status = True
                profile.save()
                
                # Make sure user is active
                user.is_active = True
                user.save()
                
                self.stdout.write(self.style.SUCCESS(f'✓ Profile completed for {user.username}'))
                self.stdout.write(self.style.WARNING(f'⚠ Remember to setup MFA at /accounts/mfa/setup/ after first login!'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ All superuser profiles are complete!\n'))
