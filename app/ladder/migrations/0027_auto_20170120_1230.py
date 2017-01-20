# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-01-20 09:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0026_auto_20170114_1744'),
    ]

    operations = [
        migrations.CreateModel(
            name='LadderSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_season', models.PositiveSmallIntegerField(default=1)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='match',
            name='season',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='scorechange',
            name='season',
            field=models.PositiveSmallIntegerField(default=1),
        ),
    ]
