from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("foodcartapp", "0051_alter_order_payment_method"),
        ("geocoder_cache", "0002_alter_geocodercache_address_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="restaurant",
            name="latitude",
        ),
        migrations.RemoveField(
            model_name="restaurant",
            name="longitude",
        ),
        migrations.AddField(
            model_name="restaurant",
            name="location",
            field=models.OneToOneField(
                to="geocoder_cache.GeocoderCache",
                verbose_name="координаты",
                null=True,
                blank=True,
                on_delete=models.SET_NULL,
                help_text="Координаты ресторана (широта/долгота)",
            ),
        ),
    ] 