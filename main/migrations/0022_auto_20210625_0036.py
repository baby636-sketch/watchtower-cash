# Generated by Django 3.0.14 on 2021-06-25 00:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0021_transaction_address_fk'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='transaction',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='address',
        ),
    ]
