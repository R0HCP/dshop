# Generated by Django 5.1.6 on 2025-03-25 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='isTrusted',
            field=models.BooleanField(default=True),
        ),
    ]
