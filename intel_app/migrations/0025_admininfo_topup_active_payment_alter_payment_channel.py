# Generated by Django 5.1a1 on 2024-07-01 22:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intel_app', '0024_alter_admininfo_active_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='admininfo',
            name='topup_active_payment',
            field=models.CharField(choices=[('Direct', 'Direct'), ('Paystack', 'Paystack'), ('AppsNMobile', 'AppsNMobile')], default='Direct', max_length=250),
        ),
        migrations.AlterField(
            model_name='payment',
            name='channel',
            field=models.CharField(blank=True, choices=[('mtn', 'mtn'), ('ishare', 'ishare'), ('bigtime', 'bigtime'), ('telecel', 'telecel'), ('afa', 'afa'), ('topup', 'topup')], max_length=250, null=True),
        ),
    ]
