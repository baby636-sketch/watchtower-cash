# Generated by Django 3.0.7 on 2021-03-26 01:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20210321_0303'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='subscribed',
        ),
    ]
