# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-26 14:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0002_auto_20160225_2132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='algorithm',
            name='formula',
            field=models.CharField(max_length=2500),
        ),
    ]