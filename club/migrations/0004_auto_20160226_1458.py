# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-26 14:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0003_auto_20160226_1445'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ladder',
            old_name='rating_algorithm',
            new_name='algorithm',
        ),
    ]