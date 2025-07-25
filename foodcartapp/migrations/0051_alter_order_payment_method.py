# Generated by Django 5.2.4 on 2025-07-21 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("foodcartapp", "0050_restaurant_latitude_restaurant_longitude"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                blank=True,
                choices=[("online", "Онлайн"), ("cash", "Наличными")],
                max_length=20,
                null=True,
                verbose_name="способ оплаты",
            ),
        ),
    ]
