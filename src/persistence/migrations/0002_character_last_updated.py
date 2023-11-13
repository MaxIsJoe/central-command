# Generated by Django 3.2.22 on 2023-11-11 22:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('persistence', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='last_updated',
            field=models.DateTimeField(auto_now=True, help_text='When was this character last updated? Useful for conciliation with the local cache of a character.'),
        ),
    ]
