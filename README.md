Django SHOP payment backend for [Payer](http://payer.se). Uses [python-payer-api](https://github.com/dessibelle/python-payer-api) for interacting with the API.


Installation
============

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
=============

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

SHOP_PAYER_BACKEND_HIDE_DETAILS = False     # Hide order details during payment
SHOP_PAYER_BACKEND_DEBUG_MODE = 'verbose'   # 'silent', 'brief'
SHOP_PAYER_BACKEND_TEST_MODE = True
```

Extensibility
=============

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

[![Build Status](https://travis-ci.org/dessibelle/django-shop-payer-backend.svg?branch=master)](https://travis-ci.org/dessibelle/django-shop-payer-backend)
