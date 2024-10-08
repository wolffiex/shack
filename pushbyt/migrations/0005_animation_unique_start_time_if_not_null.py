# Generated by Django 5.0.4 on 2024-05-11 14:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pushbyt", "0004_alter_animation_source"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="animation",
            constraint=models.UniqueConstraint(
                condition=models.Q(("start_time__isnull", False)),
                fields=("start_time",),
                name="unique_start_time_if_not_null",
            ),
        ),
    ]
