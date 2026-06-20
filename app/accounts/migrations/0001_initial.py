

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('USER', 'Regular User'), ('STAFF', 'Staff/Department Officer'), ('ADMIN', 'Administrator')], default='USER', max_length=20)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('address', models.TextField(blank=True)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('postal_code', models.CharField(blank=True, max_length=20)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('is_email_verified', models.BooleanField(default=False)),
                ('email_verification_token', models.CharField(blank=True, max_length=100)),
                ('email_verification_sent_at', models.DateTimeField(blank=True, null=True)),
                ('receive_email_notifications', models.BooleanField(default=True)),
                ('receive_sms_notifications', models.BooleanField(default=False)),
                ('dark_mode', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_login_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'User Profiles',
            },
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('LOGIN', 'Login'), ('LOGOUT', 'Logout'), ('COMPLAINT_SUBMIT', 'Complaint Submitted'), ('COMPLAINT_UPDATE', 'Complaint Updated'), ('COMPLAINT_VIEW', 'Complaint Viewed'), ('STATUS_CHANGE', 'Status Changed'), ('ADMIN_ACTION', 'Admin Action'), ('PROFILE_UPDATE', 'Profile Updated')], max_length=50)),
                ('description', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['user', '-timestamp'], name='accounts_ac_user_id_9bf4ca_idx'), models.Index(fields=['action_type'], name='accounts_ac_action__d504cb_idx')],
            },
        ),
    ]
