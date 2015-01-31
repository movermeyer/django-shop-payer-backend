from django.conf import settings
from payer_api.order import (
    PayerBuyerDetails,
    PayerOrderItem,
)
from shop.models import AddressModel
from shop.addressmodel.models import ADDRESS_TEMPLATE
import django.dispatch
import re


VAT_PERCENTAGE = getattr(settings, 'SHOP_PAYER_BACKEND_DEFAULT_VAT', 25)

populate_buyer_details_dict = django.dispatch.Signal(providing_args=[
    "buyer_details_dict",
    "user",
    "address",
    "order"])
populate_order_item_dict = django.dispatch.Signal(providing_args=[
    "order_item_dict",
    "order_item",
    "extra_order_price"])
determine_order_address = django.dispatch.Signal(providing_args=[
    "address",
    "order",
    "user"])


def payer_order_item_from_order_item(order_item):

    order_item_dict = {
        'description': order_item.product_name,
        'price_including_vat': order_item.unit_price,
        'vat_percentage': VAT_PERCENTAGE,
        'quantity': order_item.quantity,
    }

    populate_order_item_dict.send(sender=None, order_item_dict=order_item_dict, order_item=order_item,
                                  extra_order_price=None)

    return PayerOrderItem(**order_item_dict)


def payer_order_item_from_extra_order_price(extra_order_price):

    order_item_dict = {
        'description': extra_order_price.label,
        'price_including_vat': extra_order_price.value,
        'vat_percentage': VAT_PERCENTAGE,
        'quantity': 1,
    }

    populate_order_item_dict.send(sender=None, order_item_dict=order_item_dict, order_item=None,
                                  extra_order_price=extra_order_price)

    return PayerOrderItem(**order_item_dict)


def buyer_details_from_user(user, order=None):

    first_name = last_name = address = None

    try:
        # Extract address object from user
        address = AddressModel.objects.filter(user_billing=user)[0]
    except:
        pass

    # Override address object via signal
    determine_order_address.send(sender=None, address=address, order=order, user=user)

    try:
        # Extract address details from address object
        assert address

        first_name, last_name = AddressFormatParser.get_first_and_last_name(address.name)
        address_details = {
            'address_line_1': address.address,
            'address_line_2': address.address2,
            'postal_code': address.zip_code,
            'city': address.city,
        }
    except:
        # Extract address details from order.billing_address_text
        parser = AddressFormatParser(order.billing_address_text, ADDRESS_TEMPLATE)
        address_details = parser.get_payer_vars()

    try:
        # Make sure, in the end, we actually do have address details
        assert address_details
    except:
        raise Exception("Could not determine address")

    buyer_details_dict = {
        'first_name': first_name or user.first_name,
        'last_name': last_name or user.last_name,
        'address_line_1': None,
        'address_line_2': None,
        'postal_code': None,
        'city': None,
        'country_code': None,
        'phone_home': None,
        'phone_work': None,
        'phone_mobile': None,
        'email': user.email,
        'organisation': None,
        'orgnr': None,
        'customer_id': None,
    }

    buyer_details_dict.update(address_details)

    # Override gathered address details using signal
    populate_buyer_details_dict.send(sender=None, buyer_details_dict=buyer_details_dict, user=user,
                                     address=address, order=order)

    return PayerBuyerDetails(**buyer_details_dict)


class AddressFormatParser(object):
    """This class does a reverse parse of a string created using a
    specified format string, e.g. a django SHOP address and the
    SHOP_ADDRESS_TEMPLATE string respectively.

    Given an address string and a format it will try to match each
    format key to a part of the string and return the values in a
    dict with format keys as dict keys and the string value as the
    dict value."""

    def __init__(self, address_string, format_string):
        self.address = address_string
        self.fmt = format_string

    def _get_format_vars(self, fmt):
        class Mapper(object):
            def __init__(self):
                self.vars = []

            def __getitem__(self, item):
                self.vars.append(item)
                return item

        mapper = Mapper()
        fmt % mapper

        return mapper.vars

    def _get_format_mapping(self, fmt):
        lines = fmt.split("\n")

        line_fmt = []
        line_vars = []
        for l in lines:
            line_fmt.append(tuple(re.split(r'(%\([^\)]+\)s)', l)))
            line_vars.append(tuple(self._get_format_vars(l)))

        return line_fmt, line_vars

    def get_address_vars(self):
        line_fmt, line_vars = self._get_format_mapping(self.fmt)
        lines = self.address.split("\n")

        address_vars = {}

        for idx, l in enumerate(lines):
            fmt = line_fmt[idx]
            keys = line_vars[idx]

            regex = r""
            key_idx = -1
            for var in fmt:

                if not len(self._get_format_vars(var)):
                    regex += r"" + var + ""
                else:
                    key_idx += 1
                    key = keys[key_idx]
                    regex += r"(?P<" + key + ">.+?)"

            m = re.match(regex, l)

            if m and m.groups():
                values = list(m.groups())

                while len(values) < len(keys):
                    values.append('')

                address_vars.update(dict(zip(keys, values)))

        return address_vars

    def get_payer_vars(self):
        address_vars = self.get_address_vars()

        name = address_vars.get('name', None)
        if name:
            first_name, last_name = self.get_first_and_last_name(name)

        if first_name or last_name:
            address_vars.update({
                'first_name': first_name,
                'last_name': last_name,
            })
            address_vars.pop('name', None)

        key_mapping = {
            'address': 'address_line_1',
            'zipcode': 'postal_code',
            'city': 'city',
        }

        for old, new in key_mapping.iteritems():
            address_vars[new] = address_vars.pop(old, None)

        return address_vars

    @classmethod
    def get_first_and_last_name(cls, name):
        # Split name in equally large lists
        first_name = last_name = None
        seq = name.split(" ")
        if len(seq) > 1:
            size = len(seq) / 2
            first_name, last_name = tuple([" ".join(seq[i:i + size]) for i in range(0, len(seq), size)])

        return first_name, last_name
