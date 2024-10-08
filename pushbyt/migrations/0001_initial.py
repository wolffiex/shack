# Generated by Django 5.0.4 on 2024-05-06 20:30

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Lock",
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
                ("name", models.CharField(max_length=100, unique=True)),
                ("acquired", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Animation",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "file_path",
                    models.FilePathField(blank=True, null=True, path="render"),
                ),
                ("start_time", models.DateTimeField()),
                (
                    "served_at",
                    models.DateTimeField(blank=True, default=None, null=True),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["start_time"], name="pushbyt_ani_start_t_584240_idx"
                    )
                ],
            },
        ),
    ]
