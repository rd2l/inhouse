# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-01-13 10:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0024_auto_20170111_1817'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='banned',
            field=models.BooleanField(default=False),
        ),
    ]
