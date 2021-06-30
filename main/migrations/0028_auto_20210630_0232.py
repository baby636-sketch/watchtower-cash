# Generated by Django 3.0.14 on 2021-06-30 02:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_remove_transaction_spend_block_height'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='tokenid',
            field=models.CharField(blank=True, db_index=True, max_length=70, unique=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='source',
            field=models.CharField(db_index=True, max_length=100),
        ),
    ]
