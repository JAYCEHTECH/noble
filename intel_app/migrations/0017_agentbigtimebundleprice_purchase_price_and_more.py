# Generated by Django 5.0 on 2024-05-24 09:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intel_app', '0016_profitinstance_bigtimebundleprice_purchase_price_and_more'),
    ]

    operations = [
        # migrations.AddField(
        #     model_name='agentbigtimebundleprice',
        #     name='purchase_price',
        #     field=models.FloatField(blank=True, null=True),
        # ),
        # migrations.AddField(
        #     model_name='agentisharebundleprice',
        #     name='purchase_price',
        #     field=models.FloatField(blank=True, null=True),
        # ),
        # migrations.AddField(
        #     model_name='agentmtnbundleprice',
        #     name='purchase_price',
        #     field=models.FloatField(blank=True, null=True),
        # ),
        # migrations.AddField(
        #     model_name='superagentbigtimebundleprice',
        #     name='purchase_price',
        #     field=models.FloatField(blank=True, null=True),
        # ),
        # migrations.AddField(
        #     model_name='superagentisharebundleprice',
        #     name='purchase_price',
        #     field=models.FloatField(blank=True, null=True),
        # ),
        # migrations.AddField(
        #     model_name='superagentmtnbundleprice',
        #     name='purchase_price',
        #     field=models.FloatField(blank=True, null=True),
        # ),
        migrations.CreateModel(
            name='WalletTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(blank=True, choices=[('Debit', 'Debit'), ('Credit', 'Credit')], max_length=250, null=True)),
                ('transaction_date', models.DateTimeField(auto_now_add=True)),
                ('transaction_use', models.CharField(blank=True, max_length=250, null=True)),
                ('transaction_amount', models.FloatField()),
                ('new_balance', models.FloatField(null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
