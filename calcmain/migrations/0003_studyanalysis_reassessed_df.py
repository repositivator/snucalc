# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-01 00:09
from __future__ import unicode_literals

from django.db import migrations
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('calcmain', '0002_probexcelsheets'),
    ]

    operations = [
        migrations.AddField(
            model_name='studyanalysis',
            name='reassessed_df',
            field=picklefield.fields.PickledObjectField(default='None', editable=False),
        ),
    ]