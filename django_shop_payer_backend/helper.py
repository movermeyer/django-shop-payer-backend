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


populate_buyer_dict = django.dispatch.Signal(providing_args=["user", "address", "order"])


def payer_order_item_from_order_item(order_item):
    return PayerOrderItem(
        description=order_item.product_name,
        price_including_vat=order_item.line_total,
        vat_percentage=getattr(settings, 'SHOP_PAYMENT_BACKEND_PAYER_DEFAULT_VAT', 25),
        quantity=order_item.quantity,
    )


def buyer_details_from_user(user, order=None):

    try:
        shop_address = AddressModel.objects.filter(user_shipping=user)[0]
    except:
        raise Exception("Could not determine address")

    # Split name in equally large lists
    first_name = last_name = ''
    seq = shop_address.name.split(" ")
    if len(seq) > 1:
        size = len(seq) / 2
        first_name, last_name = tuple([" ".join(seq[i:i+size]) for i  in range(0, len(seq), size)])

    buyer_dict = {
        'first_name': user.first_name or first_name,
        'last_name': user.last_name or last_name,
        'address_line_1': shop_address.address,
        'address_line_2': shop_address.address2,
        'postal_code': shop_address.zip_code,
        'city': shop_address.city,
        'email': user.email,
    }

    populate_buyer_dict.send(sender=PayerBuyerDetails, buyer_dict=buyer_dict, user=user, address=shop_address, order="order")

    return PayerBuyerDetails(**buyer_dict)


