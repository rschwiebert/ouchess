# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-19 21:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0006_auto_20160219_2124'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ladder',
            name='event_type',
        ),
    ]
