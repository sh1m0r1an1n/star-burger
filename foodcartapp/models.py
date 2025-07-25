from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import F, Sum
from decimal import Decimal
from collections import defaultdict


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def with_total_cost(self):
        return self.annotate(
            total_cost=Sum(F('items__quantity') * F('items__price'))
        )

    def with_available_restaurants(self):
        """Добавляет к каждому заказу список ресторанов, которые могут выполнить заказ. Возвращает self."""
        menu_items = RestaurantMenuItem.objects.filter(availability=True).select_related('restaurant', 'product')
        restaurants_products = defaultdict(set)
        for item in menu_items:
            restaurants_products[item.restaurant].add(item.product)

        for order in self:
            order_products = set(order_item.product for order_item in order.items.select_related('product'))
            available_restaurants = []
            for restaurant, products in restaurants_products.items():
                if order_products.issubset(products):
                    available_restaurants.append(restaurant)
            order.available_restaurants = available_restaurants
        return self


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтверждён'),
        ('preparing', 'Готовится'),
        ('delivering', 'В пути'),
        ('completed', 'Выполнен'),
    ]
    
    PAYMENT_CHOICES = [
        ('online', 'Онлайн'),
        ('cash', 'Наличными'),
    ]
    
    firstname = models.CharField(
        'имя',
        max_length=50
    )
    lastname = models.CharField(
        'фамилия',
        max_length=50
    )
    phonenumber = PhoneNumberField(
        'номер телефона'
    )
    address = models.CharField(
        'адрес доставки',
        max_length=200
    )
    status = models.CharField(
        'статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
    )
    payment_method = models.CharField(
        'способ оплаты',
        max_length=20,
        choices=PAYMENT_CHOICES,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        'время создания',
        auto_now_add=True
    )
    comment = models.TextField(
        'комментарий',
        blank=True,
        help_text='Комментарий к заказу (аллергии, особые пожелания и т.д.)'
    )
    called_at = models.DateTimeField(
        'дата звонка',
        null=True,
        blank=True,
        help_text='Дата и время звонка клиенту'
    )
    delivered_at = models.DateTimeField(
        'дата доставки',
        null=True,
        blank=True,
        help_text='Дата и время доставки заказа'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='ресторан',
        related_name='orders',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text='Ресторан, который будет готовить заказ'
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phonenumber']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['called_at']),
            models.Index(fields=['delivered_at']),
        ]

    def __str__(self):
        return f"Заказ {self.pk} - {self.firstname} {self.lastname}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='заказ'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='товар'
    )
    quantity = models.PositiveIntegerField(
        'количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
