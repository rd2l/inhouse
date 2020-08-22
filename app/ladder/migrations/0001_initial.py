# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-11-28 09:15


from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('rank', models.PositiveIntegerField()),
                ('score', models.PositiveIntegerField()),
                ('mmr', models.PositiveIntegerField()),
                ('dota_id', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ['rank'],
            },
        ),
    ]
