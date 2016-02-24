# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-19 21:24
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0005_auto_20160219_2058'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Event',
            new_name='Ladder',
        ),
        migrations.RenameField(
            model_name='game',
            old_name='event',
            new_name='ladder',
        ),
        migrations.RenameField(
            model_name='rating',
            old_name='event',
            new_name='ladder',
        ),
        migrations.AlterUniqueTogether(
            name='rating',
            unique_together=set([('player', 'ladder')]),
        ),
    ]