from django.contrib import admin
from django.shortcuts import reverse, redirect
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlencode

from .models import Product
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem
from .models import Order
from .models import OrderItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'quantity', 'get_fixed_price', 'get_total_price']
    readonly_fields = ['get_fixed_price', 'get_total_price']

    def get_fixed_price(self, obj):
        if obj.price:
            return f"{obj.price} ₽"
        return "—"
    get_fixed_price.short_description = 'зафиксированная цена'

    def get_total_price(self, obj):
        if obj.price:
            total = obj.price * obj.quantity
            return f"{total} ₽"
        return "—"
    get_total_price.short_description = 'общая стоимость'

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if instance.product and not instance.price:
                instance.price = instance.product.price
        formset.save()
        super().save_formset(request, form, formset, change)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'pk',
        'firstname',
        'lastname',
        'phonenumber',
        'status',
        'payment_method',
        'restaurant',
        'comment',
        'created_at',
        'called_at',
        'delivered_at'
    ]
    list_display_links = ['pk', 'firstname']
    search_fields = [
        'firstname',
        'lastname',
        'phonenumber',
        'address'
    ]
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at']
    inlines = [OrderItemInline]

    fieldsets = (
        ('Контактная информация', {
            'fields': [
                'firstname',
                'lastname',
                'phonenumber',
                'address'
            ]
        }),
        ('Статус заказа', {
            'fields': ['status', 'payment_method']
        }),
        ('Комментарий', {
            'fields': ['comment'],
            'classes': ['wide']
        }),
        ('Даты выполнения', {
            'fields': ['called_at', 'delivered_at'],
            'classes': ['wide']
        }),
        ('Ресторан', {
            'fields': ['restaurant'],
        }),
        ('Служебная информация', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    )

    def response_change(self, request, obj):
        """Перенаправляет на страницу, указанную в параметре next, после сохранения заказа"""
        response = super().response_change(request, obj)
        
        next_url = request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=request.get_host()):
            return redirect(next_url)
        
        return response
