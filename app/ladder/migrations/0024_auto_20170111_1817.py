# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-01-11 15:17


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0023_auto_20170111_1807'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='blacklist',
            field=models.ManyToManyField(related_name='blacklisted_by', to='ladder.Player'),
        ),
    ]
