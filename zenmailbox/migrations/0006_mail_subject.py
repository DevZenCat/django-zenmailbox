# Generated by Django 3.0.4 on 2020-12-28 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zenmailbox', '0005_auto_20201113_0536'),
    ]

    operations = [
        migrations.AddField(
            model_name='mail',
            name='subject',
            field=models.CharField(default='None', max_length=255),
            preserve_default=False,
        ),
    ]