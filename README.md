Django SHOP Payer Backend
=========================

[![Build Status](https://travis-ci.org/dessibelle/django-shop-payer-backend.svg?branch=master)](https://travis-ci.org/dessibelle/django-shop-payer-backend) [![Coverage Status](https://coveralls.io/repos/dessibelle/django-shop-payer-backend/badge.svg)](https://coveralls.io/r/dessibelle/django-shop-payer-backend) [![Latest Version](https://pypip.in/version/django-shop-payer-backend/badge.svg?style=flat)](https://pypi.python.org/pypi/django-shop-payer-backend/)

Django SHOP payment backend for [Payer](http://payer.se). Uses [python-payer-api](https://github.com/dessibelle/python-payer-api) for interacting with the API.


Installation
------------

	pip install django-shop-payer-backend

Add to installed apps

```python
INSTALLED_APPS = [
    ...
    'polymorphic',
    'shop'
    'shop.addressmodel',
    'django_shop_payer_backend',
    ...
]
```

Configure one ore more payment backends

```python
SHOP_PAYMENT_BACKENDS = [
    'django_shop_payer_backend.backends.PayerCreditCardPaymentBackend',
    'django_shop_payer_backend.backends.PayerBankPaymentBackend',
    'django_shop_payer_backend.backends.PayerInvoicePaymentBackend',
    'django_shop_payer_backend.backends.PayerPhonePaymentBackend',
]
```

You could also use the `GenericPayerBackend` in order to let the user choose
payment method *after* being redirected to Payer, or define a subclass of your
own, listing a custom set of methods in the `payment_methods` property. This
might be a good option if you are using the Payer backend along with other
backends such as Paypal etc. 


Configuration
-------------

Add your keys to settings.py

```python
SHOP_PAYER_BACKEND_AGENT_ID = "AGENT_ID"
SHOP_PAYER_BACKEND_ID1 = "6866ef97a972ba3a2c6ff8bb2812981054770162"
SHOP_PAYER_BACKEND_ID2 = "1388ac756f07b0dda2961436ba8596c7b7995e94"
```

The following settings are optional

```python    
# Used for white/blacklisting callback IPs
SHOP_PAYER_BACKEND_IP_WHITELIST = ["192.168.0.1"]
SHOP_PAYER_BACKEND_IP_BLACKLIST = ["10.0.1.1"] 
# Used for suppliying an address model
SHOP_PAYER_BACKEND_ADDRESS_HANDLER = 'project.app.path.to.address_model_callback'

SHOP_PAYER_BACKEND_HIDE_DETAILS = False     # Hide order details during payment
SHOP_PAYER_BACKEND_DEBUG_MODE = 'verbose'   # 'silent', 'brief'
SHOP_PAYER_BACKEND_TEST_MODE = True
```

Considerations
--------------

Due to the fact that django SHOP by default does not store any relation between
the Order model and the AddressModel model there is no good way for payment backends
to determine the shipping/billing address for a given order. For some backends this
might not be an issue, but in this case Payer expects to address data in the  order
details. 

django-shop-payer-backend tries to tackle by determining the order (billing) address
using the following strategy:

1. Try to fetch AddressModel from current user (if `user.is_authenticated()`).
1. Try to load an AddressModel using a callback supplied in the `SHOP_PAYER_BACKEND_ADDRESS_HANDLER` setting.
1. Try to extract address details from `order.billing_address_text` by reverse parsing the address template used by django SHOP.
1. Let you override/complete the data returned using the above methods using the `populate_buyer_details_dict` signal.

This has two implications:

1. For non-authenticated users it is simply not possible get an AddressModel object using the default setup. In this case a reverse parsing of the address template string django SHOP uses to store the textual address representation on the Order object. Due to the somewhat fragile nature of this parsing method, you should take extreme precautions when modifying the `SHOP_ADDRESS_TEMPLATE` setting. For the parser to function it is recommended that you use some form identifying "key" to identify each keyword (as with "Name:"" etc. in the default pattern). Patterns such as `%(name)s, %(address)s,[...]` will likely fail as there is nothing differentiating the `name` and `address` keywords in the string format, and alas the regexp will not be able to identify the keywords correctly.
1. Fields supported by the Payer API that do not have an obvious counterpart on the AddressModel model (e.g. email, phone, organisation, etc.) will unsurprisingly not be included in the PayerBuyerDetails data using the default settings. To make sure they are included, use the methods described in the *Extensibility* section below.

The way to tackle both of the issues outlined above, is probably to add a foreign key to AddressModel on Order and store the object used when setting `order.billing_address_text`. That way you could add a address model callback handler (described below), which will let you return that (or any other) object to the backend.

Extensibility
-------------

Let's say you have a custom address model based on `shop.addressmodel.models.Address`
which adds the field `company`. Naturally you would want this data sent to Payer as
well, in order to have it appear on invoices etc. To accomplish that, add a 
receiver for the `populate_buyer_details_dict` signal and update the buyer details
dict like so:

```python
from django_shop_payer_backend.helper import populate_buyer_details_dict
from django.dispatch import receiver

@receiver(populate_buyer_details_dict)
def add_additional_buyer_details(sender, **kwargs):

    buyer_details_dict = kwargs.get('buyer_details_dict', None)
    user = kwargs.get('user', None)
    address = kwargs.get('address', None)
    order = kwargs.get('order', None)

    buyer_details_dict.update({
        'organisation': address.company,
    })
```

There is a similar signal, `populate_order_item_dict`, for order items, allowing you
to modify the data that before the PayerOrderItem object is initialized. This can be
useful for example if your Product model has a field holding VAT percentages, in
which case you could inject that value using this method.

Another option for supplying an address to the backend is to implement and address
callback handler, and return an AddressModel object. This is a good option if you
are using a custom Order model that has foreign keys to the AddressModel. In that
case, you can implement a callback something along the lines of the following:

```python
def address_model_callback(*args, **kwargs):

    address = kwargs.get('address', None)
    order = kwargs.get('order', None)

    if address is None and order is not None:
        try:
            address = order.billing_address
        except Exception:
            pass

    return address
```

And add the following to `settings.py`:

```python
SHOP_PAYER_BACKEND_ADDRESS_HANDLER = 'project.app.path.to.address_model_callback'
```
