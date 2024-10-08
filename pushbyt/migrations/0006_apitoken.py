# Generated by Django 5.0.4 on 2024-05-11 14:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pushbyt", "0005_animation_unique_start_time_if_not_null"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiToken",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("access_token", models.CharField(max_length=255)),
                ("refresh_token", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
