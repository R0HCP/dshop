# Generated by Django 5.1.7 on 2025-04-11 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_consultationslot_consultationbooking'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='office_latitude',
            field=models.FloatField(blank=True, null=True, verbose_name='Широта офиса'),
        ),
        migrations.AddField(
            model_name='user',
            name='office_longitude',
            field=models.FloatField(blank=True, null=True, verbose_name='Долгота офиса'),
        ),
    ]
