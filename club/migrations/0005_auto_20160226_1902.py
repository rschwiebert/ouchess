# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-26 19:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0004_auto_20160226_1458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'public'), (1, 'private')], default=0),
        ),
    ]