# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2020-09-09 08:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0042_player_new_reg_pings'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='description',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
