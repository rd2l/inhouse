# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2020-09-19 07:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0054_auto_20200919_1034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queuechannel',
            name='discord_msg',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
