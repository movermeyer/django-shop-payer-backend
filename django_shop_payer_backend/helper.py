from django.conf import settings
from payer_api.postapi import PayerPostAPI
from payer_api.order import (
    PayerProcessingControl,
    PayerBuyerDetails,
    PayerOrderItem,
    PayerOrder,
)
from shop.models import AddressModel
import django.dispatch


VAT_PERCENTAGE = getattr(settings, 'SHOP_PAYER_BACKEND_DEFAULT_VAT', 25)

populate_buyer_details_dict = django.dispatch.Signal(providing_args=["buyer_details_dict", "user", "address", "order"])
populate_order_item_dict = django.dispatch.Signal(providing_args=["order_item_dict", "order_item", "extra_order_price"])


def payer_order_item_from_order_item(order_item):

    order_item_dict = {
        'description': order_item.product_name,
        'price_including_vat': order_item.unit_price,
        'vat_percentage': VAT_PERCENTAGE,
        'quantity': order_item.quantity,
    }

    populate_order_item_dict.send(sender=PayerOrderItem, order_item_dict=order_item_dict, order_item=order_item, extra_order_price=None)

    return PayerOrderItem(**order_item_dict)


def payer_order_item_from_extra_order_price(extra_order_price):

    order_item_dict = {
        'description': extra_order_price.label,
        'price_including_vat': extra_order_price.value,
        'vat_percentage': VAT_PERCENTAGE,
        'quantity': 1,
    }

    populate_order_item_dict.send(sender=PayerOrderItem, order_item_dict=order_item_dict, order_item=None, extra_order_price=extra_order_price)

    return PayerOrderItem(**order_item_dict)

def buyer_details_from_user(user, order=None):

    try:
        shop_address = AddressModel.objects.filter(user_billing=user)[0]
    except:
        raise Exception("Could not determine address")

    # Split name in equally large lists
    first_name = last_name = ''
    seq = shop_address.name.split(" ")
    if len(seq) > 1:
        size = len(seq) / 2
        first_name, last_name = tuple([" ".join(seq[i:i+size]) for i  in range(0, len(seq), size)])

    buyer_details_dict = {
        'first_name': user.first_name or first_name,
        'last_name': user.last_name or last_name,
        'address_line_1': shop_address.address,
        'address_line_2': shop_address.address2,
        'postal_code': shop_address.zip_code,
        'city': shop_address.city,
        'country_code': None,
        'phone_home': None,
        'phone_work': None,
        'phone_mobile': None,
        'email': user.email,
        'organisation': None,
        'orgnr': None,
        'customer_id': None,
    }

    populate_buyer_details_dict.send(sender=PayerBuyerDetails, buyer_details_dict=buyer_details_dict, user=user, address=shop_address, order=order)

    return PayerBuyerDetails(**buyer_details_dict)


