# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-26 17:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import picklefield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StudyAnalysis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('study_name', models.CharField(max_length=200)),
                ('treatment_name', models.CharField(max_length=200)),
                ('imported_sheet', models.FileField(upload_to='files/imported_sheets')),
                ('up_patients', models.IntegerField()),
                ('processed_df', picklefield.fields.PickledObjectField(default='None', editable=False)),
                ('createdAt', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]