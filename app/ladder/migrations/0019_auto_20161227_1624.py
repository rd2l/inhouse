# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-12-27 13:24


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ladder', '0018_player_rank_score'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='player',
            options={'ordering': ['rank_ladder_mmr']},
        ),
        migrations.RenameField(
            model_name='player',
            old_name='rank_mmr',
            new_name='rank_ladder_mmr',
        ),
    ]
