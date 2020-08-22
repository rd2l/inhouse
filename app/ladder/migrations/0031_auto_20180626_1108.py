# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-06-26 08:08


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0030_auto_20180625_1116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='banned',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(None, 'Not banned'), (1, 'Banned from playing only'), (2, 'Banned from playing and lobby')], null=True),
        ),
    ]
