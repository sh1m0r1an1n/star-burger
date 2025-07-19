import json
from django.templatetags.static import static
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from phonenumber_field.phonenumber import to_python

from .models import Product, Order, OrderItem


@api_view(['GET'])
def banners_list_api(request):
    # FIXME move data to db?
    return Response([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ])


@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return Response(dumped_products)


@api_view(['POST'])
def register_order(request):
    order_data = request.data
    
    required_fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
    
    missing_fields = [field for field in required_fields if field not in order_data]
    if missing_fields:
        return Response(
            {field: 'Обязательное поле.' for field in missing_fields},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    null_fields = [field for field in required_fields if order_data[field] is None]
    if null_fields:
        return Response(
            {field: 'Это поле не может быть пустым.' for field in null_fields},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    string_fields = ['firstname', 'lastname', 'address']
    for field in string_fields:
        if not isinstance(order_data[field], str):
            return Response(
                {field: 'Not a valid string.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if order_data[field].strip() == '':
            return Response(
                {field: 'Это поле не может быть пустым.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if order_data['phonenumber'].strip() == '':
        return Response(
            {'phonenumber': 'Это поле не может быть пустым.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    phone_number = to_python(order_data['phonenumber'])
    if phone_number is None or not phone_number.is_valid():
        return Response(
            {'phonenumber': 'Введен некорректный номер телефона.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    products = order_data['products']
    if not isinstance(products, list):
        return Response(
            {'products': f'Ожидался list со значениями, но был получен "{type(products).__name__}".'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(products) == 0:
        return Response(
            {'products': 'Этот список не может быть пустым.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    for i, product_data in enumerate(products):
        if not isinstance(product_data, dict):
            return Response(
                {'products': f'Элемент {i}: ожидался dict, но был получен {type(product_data).__name__}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'product' not in product_data:
            return Response(
                {'products': f'Элемент {i}: отсутствует обязательное поле "product".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'quantity' not in product_data:
            return Response(
                {'products': f'Элемент {i}: отсутствует обязательное поле "quantity".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            Product.objects.get(id=product_data['product'])
        except Product.DoesNotExist:
            return Response(
                {'products': f'Недопустимый первичный ключ "{product_data["product"]}"'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    print(order_data)
    
    with transaction.atomic():
        order = Order.objects.create(
            firstname=order_data['firstname'],
            lastname=order_data['lastname'], 
            phonenumber=order_data['phonenumber'],
            address=order_data['address']
        )
        
        for product_data in products:
            product = Product.objects.get(id=product_data['product'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=product_data['quantity']
            )
    
    return Response({'status': 'success'})
