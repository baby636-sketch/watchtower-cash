# Generated by Django 3.0.7 on 2020-09-04 05:56

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0040_bchaddress_scanned'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriber',
            name='telegram_user_details',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict),
        ),
    ]
