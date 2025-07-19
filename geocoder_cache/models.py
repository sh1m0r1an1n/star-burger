from django.db import models


class GeocoderCache(models.Model):
    """Кэш для хранения ответов геокодера"""
    
    address = models.CharField(
        'адрес',
        max_length=200,
        unique=True,
    )
    latitude = models.FloatField(
        'широта',
        null=True,
        blank=True,
    )
    longitude = models.FloatField(
        'долгота',
        null=True,
        blank=True,
    )
    requested_at = models.DateTimeField(
        'дата запроса',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'кэш геокодера'
        verbose_name_plural = 'кэш геокодера'
        indexes = [
            models.Index(fields=['address']),
            models.Index(fields=['requested_at']),
        ]

    def __str__(self):
        return f"{self.address} ({self.latitude}, {self.longitude})"
