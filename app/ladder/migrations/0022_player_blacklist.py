# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-01-11 11:46


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0021_player_bot_access'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='blacklist',
            field=models.ManyToManyField(related_name='_player_blacklist_+', to='ladder.Player'),
        ),
    ]
