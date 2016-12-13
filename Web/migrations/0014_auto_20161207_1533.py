# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-07 15:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Web', '0013_auto_20161207_1500'),
    ]

    operations = [
        migrations.AddField(
            model_name='netinterface',
            name='eth0_ip',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='netinterface',
            name='eth1_ip',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='netinterface',
            name='eth2_ip',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='netinterface',
            name='eth3_ip',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='network',
            name='ip',
            field=models.CharField(default='0.0.0.0', max_length=16),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='network',
            name='lower_ip',
            field=models.CharField(default='0.0.0.0', max_length=16),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='network',
            name='netmask',
            field=models.CharField(default='255.255.255.255', max_length=16),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='network',
            name='upper_ip',
            field=models.CharField(default='0.0.0.0', max_length=16),
            preserve_default=False,
        ),
    ]