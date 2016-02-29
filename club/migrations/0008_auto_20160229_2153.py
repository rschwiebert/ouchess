# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-29 21:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0007_auto_20160227_1224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='datetime',
            field=models.DateTimeField(auto_now_add=True, help_text='NOTE: game time MUST be sufficient to place it in sufficiently correct chronological order with other games.', null=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='time_control',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
    ]