# Generated by Django 5.2 on 2025-07-19 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("foodcartapp", "0044_alter_order_status_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="comment",
            field=models.TextField(
                blank=True,
                help_text="Комментарий к заказу (аллергии, особые пожелания и т.д.)",
                verbose_name="комментарий",
            ),
        ),
    ]
