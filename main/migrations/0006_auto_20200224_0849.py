# Generated by Django 3.0.3 on 2020-02-24 08:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_transaction_date_created'),
    ]

    operations = [
        migrations.RenameField(
            model_name='blockheight',
            old_name='createdby',
            new_name='created_datetime',
        ),
        migrations.RenameField(
            model_name='blockheight',
            old_name='updatedby',
            new_name='updated_datetime',
        ),
        migrations.RenameField(
            model_name='transaction',
            old_name='date_created',
            new_name='created_datetime',
        ),
    ]
