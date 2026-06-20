from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Creates missing UserProfile and API tokens for existing users'

    def handle(self, *args, **options):
        created = 0
        for user in User.objects.all():
            try:
                user.profile
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user)
                self.stdout.write(f'  Created profile for: {user.username}')
                created += 1

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created {created} missing profile(s)'))
        else:
            self.stdout.write('All users already have profiles')

        tokens_created = 0
        for user in User.objects.all():
            from rest_framework.authtoken.models import Token
            try:
                user.auth_token
            except Token.DoesNotExist:
                Token.objects.create(user=user)
                tokens_created += 1

        if tokens_created:
            self.stdout.write(self.style.SUCCESS(f'Created {tokens_created} missing API token(s)'))
        else:
            self.stdout.write('All users already have API tokens')
