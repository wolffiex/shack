# Generated by Django 5.0.4 on 2024-05-11 16:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pushbyt", "0007_apitoken_expires_in"),
    ]

    operations = [
        migrations.AlterField(
            model_name="animation",
            name="metadata",
            field=models.JSONField(),
        ),
    ]
