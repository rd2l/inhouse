# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-12-28 09:45


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0019_auto_20161227_1624'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='voice_issues',
            field=models.BooleanField(default=False),
        ),
    ]
