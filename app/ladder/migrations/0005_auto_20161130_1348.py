# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-11-30 10:48


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0004_auto_20161130_1308'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='matchplayer',
            unique_together=set([('player', 'match')]),
        ),
    ]
