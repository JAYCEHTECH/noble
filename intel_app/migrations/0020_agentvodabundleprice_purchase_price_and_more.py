# Generated by Django 5.1a1 on 2024-06-29 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intel_app', '0019_superagentatcreditprice_superagentvodabundleprice'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentvodabundleprice',
            name='purchase_price',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='superagentvodabundleprice',
            name='purchase_price',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vodabundleprice',
            name='purchase_price',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
