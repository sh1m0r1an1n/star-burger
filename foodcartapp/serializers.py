from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import Product, Order, OrderItem


class OrderItemSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    
    def validate_product(self, value):
        try:
            Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError(f'Недопустимый первичный ключ "{value}"')
        return value


class OrderSerializer(serializers.Serializer):
    firstname = serializers.CharField(max_length=50)
    lastname = serializers.CharField(max_length=50)
    phonenumber = PhoneNumberField()
    address = serializers.CharField(max_length=200)
    products = OrderItemSerializer(many=True, allow_empty=False) 