# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-24 21:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0009_auto_20160224_2040'),
    ]

    operations = [
        migrations.AddField(
            model_name='ranking',
            name='initial_rating',
            field=models.IntegerField(default=1200),
        ),
    ]
