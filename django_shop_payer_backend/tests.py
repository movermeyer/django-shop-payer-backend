# -*- encoding: utf-8 -*-
from django.test import TestCase, RequestFactory
from decimal import Decimal
from helper import buyer_details_from_user

from shop.payment.api import PaymentAPI
from shop.addressmodel.models import Country
from shop.models.ordermodel import (
    Order,
    OrderItem,
    OrderExtraInfo,
    ExtraOrderItemPriceField,
    ExtraOrderPriceField,
)
from payer_api.order import PayerProcessingControl, PayerOrder
from shop.models import AddressModel, Cart
from django.contrib.auth.models import AnonymousUser
from django_shop_payer_backend.backends import GenericPayerBackend
from helper import populate_buyer_details_dict
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User


def override_address(*args, **kwargs):
    address = AddressModel.objects.create(
        name="Peter Parker",
        address="Back Street 987",
        zip_code="98765",
        city="Somewhere",
        state="N/A",
    )
    return address


class AddressHelperTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
            first_name="Mary-Jane",
            last_name="Watson")

        self.order = Order()
        self.order.order_subtotal = Decimal('10')
        self.order.order_total = Decimal('10')
        self.order.shipping_cost = Decimal('0')

        self.address = AddressModel.objects.create(
            name="Mary-Jane Watson",
            address="Main Street 123",
            address2="c/o Someone",
            zip_code="12345",
            city="Anytown",
            state="N/A",
            user_shipping=self.user,
            user_billing=self.user,
        )

        self.order.shipping_address_text = self.address.as_text()
        self.order.billing_address_text = self.address.as_text()

        self.order.save()

    def assertAddressData(self, buyer):
        self.assertEquals(buyer.first_name, "Mary-Jane")
        self.assertEquals(buyer.last_name, "Watson")
        self.assertEquals(buyer.address_line_1, "Main Street 123")
        self.assertEquals(buyer.address_line_2, "c/o Someone")
        self.assertEquals(buyer.postal_code, "12345")
        self.assertEquals(buyer.city, "Anytown")

    def add_additional_buyer_details(self, sender, **kwargs):

        buyer_details_dict = kwargs.get('buyer_details_dict', None)

        buyer_details_dict.update({
            'organisation': "The Company Inc.",
        })

    def test_anonymous_user_no_signal(self):
        buyer = buyer_details_from_user(AnonymousUser(), self.order)

        self.assertAddressData(buyer)
        self.assertEquals(buyer.email, None)

    def test_anonymous_user_with_signal(self):
        populate_buyer_details_dict.connect(self.add_additional_buyer_details)
        buyer = buyer_details_from_user(AnonymousUser(), self.order)

        self.assertAddressData(buyer)
        self.assertEquals(buyer.email, None)
        self.assertEquals(buyer.organisation, "The Company Inc.")
        populate_buyer_details_dict.disconnect(self.add_additional_buyer_details)

    def test_anonymous_user_with_address_signal(self):

        # Existing callable at path
        with self.settings(SHOP_PAYER_BACKEND_ADDRESS_HANDLER='django_shop_payer_backend.tests.override_address'):
            buyer = buyer_details_from_user(AnonymousUser(), self.order)

            self.assertEquals(buyer.first_name, "Peter")
            self.assertEquals(buyer.last_name, "Parker")
            self.assertEquals(buyer.address_line_1, "Back Street 987")
            self.assertEquals(buyer.postal_code, "98765")
            self.assertEquals(buyer.city, "Somewhere")
            self.assertEquals(buyer.email, None)

        # Inexistent callable at path
        for invalid_path in ['invalid.path']:
            with self.settings(SHOP_PAYER_BACKEND_ADDRESS_HANDLER=invalid_path):
                self.assertRaises(
                    ImportError,
                    buyer_details_from_user,
                    (AnonymousUser(), self.order,))

        from django_shop_payer_backend.helper import _import_path
        self.assertRaises(ValueError, _import_path, None)
        self.assertRaises(ValueError, _import_path, "")

    def test_auth_user_no_signal(self):
        buyer = buyer_details_from_user(self.user, self.order)

        self.assertAddressData(buyer)
        self.assertEquals(buyer.email, "test@example.com")

    def test_auth_user_with_signal(self):
        populate_buyer_details_dict.connect(self.add_additional_buyer_details)
        buyer = buyer_details_from_user(self.user, self.order)

        self.assertAddressData(buyer)
        self.assertEquals(buyer.email, "test@example.com")
        self.assertEquals(buyer.organisation, "The Company Inc.")
        populate_buyer_details_dict.disconnect(self.add_additional_buyer_details)

    def test_auth_user_without_address_no_signal(self):
        user = User.objects.create(
            username="test2",
            email="test2@example.com",
            first_name="Mary-Jane",
            last_name="Watson")
        user.save()

        buyer = buyer_details_from_user(user, self.order)

        self.assertAddressData(buyer)
        self.assertEquals(buyer.email, "test2@example.com")

    def test_auth_user_without_address_with_signal(self):
        populate_buyer_details_dict.connect(self.add_additional_buyer_details)
        buyer = buyer_details_from_user(self.user, self.order)

        self.assertAddressData(buyer)
        self.assertEquals(buyer.email, "test@example.com")
        self.assertEquals(buyer.organisation, "The Company Inc.")
        populate_buyer_details_dict.disconnect(self.add_additional_buyer_details)

    def test_address_parsing_failed(self):
        order = Order()
        order.order_subtotal = Decimal('10')
        order.order_total = Decimal('10')
        order.shipping_cost = Decimal('0')
        order.save()

        from django_shop_payer_backend.helper import AddressParsingFailedException
        self.assertRaises(AddressParsingFailedException,
                          buyer_details_from_user,
                          (AnonymousUser(), order,))
        self.assertRaises(AddressParsingFailedException,
                          buyer_details_from_user,
                          (AnonymousUser(), None,))

    def test_name_parsing(self):
        from helper import AddressFormatParser

        self.assertEquals(
            AddressFormatParser.get_first_and_last_name("Peter Parker"),
            ("Peter", "Parker",))
        self.assertEquals(
            AddressFormatParser.get_first_and_last_name("Mary Jane Watson"),
            ("Mary", "Jane Watson",))
        self.assertEquals(
            AddressFormatParser.get_first_and_last_name("Mary-Kate Olsen"),
            ("Mary-Kate", "Olsen",))
        self.assertEquals(
            AddressFormatParser.get_first_and_last_name(u"Gabriel García Márquez"),
            (u"Gabriel", u"García Márquez",))
        self.assertEquals(
            AddressFormatParser.get_first_and_last_name(u"Gabriel José de la Concordia García Márquez"),
            (u"Gabriel José De", u"La Concordia García Márquez",))
        self.assertEquals(
            AddressFormatParser.get_first_and_last_name("Kirsten Moore-Towers"),
            ("Kirsten", "Moore-Towers",))
        self.assertEquals(
            AddressFormatParser.get_first_and_last_name("Ralph Vaughan Williams"),
            ("Ralph", "Vaughan Williams",))
        self.assertEquals(
            AddressFormatParser.get_first_and_last_name("Spiderman"),
            ("Spiderman", "",))
        self.assertEquals(
            AddressFormatParser.get_first_and_last_name("P. Sherman"),
            ("P.", "Sherman",))
        self.assertEquals(
            AddressFormatParser.get_first_and_last_name("p.sherman"),
            ("P", "Sherman",))
        self.assertEquals(
            AddressFormatParser.get_first_and_last_name(None),
            ("", "",))

    def test_address_parsing(self):
        from shop.addressmodel.models import ADDRESS_TEMPLATE
        from helper import AddressFormatParser

        CUSTOM_ADDRESS_TEMPLATE = """Name: %(name)s,
Address: %(address)s,
City: %(city)s %(zipcode)s,
State: %(state)s"""

        def test_template(template):

            def filter_address_vars(address_vars, template):
                expected_keys = AddressFormatParser("", template)._get_format_vars(template)
                address_vars = dict((k, v) for k, v in address_vars.iteritems() if k in expected_keys)
                return address_vars

            # All vars
            address_vars = {
                'name': u"P. Sherman",
                'address': u"42 Wallaby Way",
                'zipcode': u"2123",
                'city': u"Sydney",
                'state': u"NSW",
                'country': u"Australia",
            }
            address_vars = filter_address_vars(address_vars, template)
            address = template % address_vars
            parser = AddressFormatParser(address, template)

            self.assertEquals(parser.get_address_vars(), address_vars)

            # Payer vars
            payer_vars = {
                'first_name': u'P.',
                'last_name': u'Sherman',
                'address_line_1': u'42 Wallaby Way',
                'postal_code': u'2123',
                'city': u'Sydney',
                'state': u'NSW',
                'country': 'Australia',
            }

            self.assertEquals(
                filter_address_vars(parser.get_payer_vars(), template),
                filter_address_vars(payer_vars, template))

            # Missing vars
            address_vars = {
                'name': u"P. Sherman",
                'address': u"42 Wallaby Way",
                'zipcode': u"2123",
                'city': u"Sydney",
                'state': u"",
                'country': u"",
            }
            address_vars = filter_address_vars(address_vars, template)
            address = template % address_vars
            parser = AddressFormatParser(address, template)

            actual_vars = dict((k, v) for k, v in parser.get_address_vars().iteritems() if v)
            expected_vars = dict((k, v) for k, v in address_vars.iteritems() if v)
            self.assertEquals(expected_vars, actual_vars)

        test_template(ADDRESS_TEMPLATE)
        test_template(CUSTOM_ADDRESS_TEMPLATE)

        # Address string None value
        parser = AddressFormatParser(None, ADDRESS_TEMPLATE)
        self.assertEqual(parser.get_address_vars(), {})


class OrderItemTestCase(TestCase):

    def setUp(self):
        from shop.models.ordermodel import OrderItem, ExtraOrderPriceField
        from shop.models import Product

        self.order = Order.objects.create(
            order_subtotal=Decimal('0'),
            order_total=Decimal('0'),
        )

        self.product = Product.objects.create(
            name="A product",
            slug='a-product',
            active=True,
            unit_price=Decimal('123.45'),
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            product_reference=self.product.get_product_reference(),
            product_name=self.product.get_name(),
            product=self.product,
            unit_price=self.product.get_price(),
            quantity=4,
            line_subtotal=self.product.get_price() * 4,
            line_total=self.product.get_price() * 4,
        )

        self.extra_order_price_field = ExtraOrderPriceField(
            order=self.order,
            label="Shipping",
            value=Decimal('12.34'),
        )

    def test_order_item_from_order_item(self):
        from helper import payer_order_item_from_order_item
        item = payer_order_item_from_order_item(self.order_item)

        # This is NOT line_subtotal/line_total, Payer does the summing.
        self.assertEquals(item.price_including_vat, 123.45)
        self.assertEquals(item.description, "A product")
        self.assertEquals(item.vat_percentage, 25.0)
        self.assertEquals(item.quantity, 4)

    def test_order_item_from_extra_order_price(self):
        from helper import payer_order_item_from_extra_order_price
        item = payer_order_item_from_extra_order_price(self.extra_order_price_field)

        self.assertEquals(item.price_including_vat, 12.34)
        self.assertEquals(item.description, "Shipping")
        self.assertEquals(item.vat_percentage, 25.0)
        self.assertEquals(item.quantity, 1)


class BaseBackendTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
            first_name="Test",
            last_name="User")

        self.shop = PaymentAPI()
        self.backend = GenericPayerBackend(shop=self.shop)

        class Mock(object):
            pass

        self.request = Mock()
        setattr(self.request, 'user', self.user)

        self.user.save()
        self.country = Country.objects.create(name='CH')
        self.address = AddressModel()
        self.address.client = self.client
        self.address.address = 'address'
        self.address.address2 = 'address2'
        self.address.zip_code = '1234'
        self.address.state = 'ZH'
        self.address.country = self.country
        self.address.is_billing = False
        self.address.is_shipping = True
        self.address.save()

        self.address2 = AddressModel()
        self.address2.client = self.client
        self.address2.address = '2address'
        self.address2.address2 = '2address2'
        self.address2.zip_code = '21234'
        self.address2.state = '2ZH'
        self.address2.country = self.country
        self.address2.is_billing = True
        self.address2.is_shipping = False
        self.address2.save()

        # The order fixture

        self.order = Order()
        self.order.user = self.user
        self.order.order_subtotal = Decimal('100')  # One item worth 100
        self.order.order_total = Decimal('120')  # plus a test field worth 10
        self.order.status = Order.PROCESSING
        ship_address = self.address
        bill_address = self.address2

        self.order.set_shipping_address(ship_address)
        self.order.set_billing_address(bill_address)
        self.order.save()

        # Orderitems
        self.orderitem = OrderItem()
        self.orderitem.order = self.order

        self.orderitem.product_name = 'Test item'
        self.orderitem.unit_price = Decimal("100")
        self.orderitem.quantity = 1

        self.orderitem.line_subtotal = Decimal('100')
        self.orderitem.line_total = Decimal('110')
        self.orderitem.save()

        oi = OrderExtraInfo()
        oi.order = self.order
        oi.text = "buffalo " * 64
        oi.save()

        eoif = ExtraOrderItemPriceField()
        eoif.order_item = self.orderitem
        eoif.label = 'Fake extra field'
        eoif.value = Decimal("10")
        eoif.save()

        eof = ExtraOrderPriceField()
        eof.order = self.order
        eof.label = "Fake Taxes"
        eof.value = Decimal("10")
        eof.save()


class FormsTestCase(BaseBackendTestCase):

    def setUp(self):
        super(FormsTestCase, self).setUp()
        from django_shop_payer_backend.forms import PayerRedirectForm
        from django_shop_payer_backend.helper import (
            payer_order_item_from_order_item,
            payer_order_item_from_extra_order_price)

        payer_order = PayerOrder(
            order_id=self.shop.get_order_unique_id(self.order),
            description="Test order",
        )
        payer_order.set_buyer_details(buyer_details_from_user(user=self.user, order=self.order))

        for order_item in self.order.items.all():
            payer_order.add_order_item(payer_order_item_from_order_item(order_item))

        for extra_order_price in self.order.extraorderpricefield_set.all():
            payer_order.add_order_item(payer_order_item_from_extra_order_price(extra_order_price))

        pc = PayerProcessingControl(
            success_redirect_url="http://host.com/shop/success/",
            authorize_notification_url="http://host.com/shop/authorize/",
            settle_notification_url="http://host.com/shop/settle/",
            redirect_back_to_shop_url="http://host.com/shop/redirect/",
        )

        self.backend.api.set_processing_control(pc)
        self.backend.api.set_order(payer_order)

        self.redirect_data = self.backend.api.get_post_data()
        self.form = PayerRedirectForm(redirect_data=self.redirect_data)

    def test_form_fields(self):
        self.assertEqual(set(self.redirect_data.keys()), set(self.form.fields.keys()))

        for key, field in self.form.fields.iteritems():
            self.assertEqual(field.initial, self.redirect_data.get(key, None))


class ConfigTestCase(TestCase):

    def test_config(self):

        from django_shop_payer_backend import check_config
        from django.conf import settings

        # Default (dummy_project) settings
        backends = getattr(settings, 'SHOP_PAYMENT_BACKENDS', [])
        backend_active = any(item.startswith('django_shop_payer_backend.backends.') for item in backends)
        self.assertTrue(backend_active)
        self.assertEqual(len(check_config(settings)), 0)

        errors = check_config(settings)
        self.assertEqual(len(errors), 0)

        # Missing Payer credentials
        setting_kwargs = {
            'SHOP_PAYMENT_BACKENDS': ["django_shop_payer_backend.backends.Backend"],
            'SHOP_PAYER_BACKEND_AGENT_ID': None,
            'SHOP_PAYER_BACKEND_ID1': None,
            'SHOP_PAYER_BACKEND_ID2': None,
        }
        with self.settings(**setting_kwargs):
            errors = check_config(settings)
            self.assertEqual(len(errors), 3)

            # Django system checks
            import django
            from distutils.version import LooseVersion

            if LooseVersion(django.get_version()) >= LooseVersion('1.7'):
                from django_shop_payer_backend import check_payment_backend_settings
                errors = check_payment_backend_settings(None)
                self.assertEqual(len(errors), 3)

        # No Payer related settings at all
        setting_kwargs = {
            'SHOP_PAYMENT_BACKENDS': [],
            'SHOP_PAYER_BACKEND_AGENT_ID': None,
            'SHOP_PAYER_BACKEND_ID1': None,
            'SHOP_PAYER_BACKEND_ID2': None,
        }
        with self.settings(**setting_kwargs):
            from django.conf import settings
            backends = getattr(settings, 'SHOP_PAYMENT_BACKENDS', [])
            backend_active = any(item.startswith('django_shop_payer_backend.backends.') for item in backends)
            self.assertFalse(backend_active)
            self.assertEqual(len(check_config(settings)), 0)


class BackendTestCase(BaseBackendTestCase):

    def setUp(self):
        super(BackendTestCase, self).setUp()
        self.factory = RequestFactory()

    def test_ip_whitelist(self):
        backend = GenericPayerBackend(shop=self.shop)
        self.assertEqual(set(backend.api.ip_whitelist),
                         set(self.backend.api.ip_whitelist))

        wl = ["192.168.0.1", "172.16.0.1", "10.0.0.1"]
        with self.settings(SHOP_PAYER_BACKEND_IP_WHITELIST=wl):
            backend = GenericPayerBackend(shop=self.shop)
            self.assertEqual(set(backend.api.ip_whitelist),
                             set(wl + self.backend.api.ip_whitelist))

    def test_ip_blacklist(self):
        backend = GenericPayerBackend(shop=self.shop)
        self.assertEqual(set(backend.api.ip_blacklist),
                         set(self.backend.api.ip_blacklist))

        wl = ["192.168.0.1", "172.16.0.1", "10.0.0.1"]
        with self.settings(SHOP_PAYER_BACKEND_IP_BLACKLIST=wl):
            backend = GenericPayerBackend(shop=self.shop)
            self.assertEqual(set(backend.api.ip_blacklist),
                             set(wl + self.backend.api.ip_blacklist))

    def test_urls(self):
        self.assertEqual(self.backend.get_url_name(), "payer")
        self.assertEqual(self.backend.get_url_name("checkout"), "payer-checkout")

        urls = self.backend.get_urls()
        self.assertEqual(len(urls), 3)

        self.assertEqual(urls[0].name, self.backend.get_url_name())
        self.assertEqual(urls[1].name, self.backend.get_url_name('authorize'))
        self.assertEqual(urls[2].name, self.backend.get_url_name('settle'))

    def test_processing_control(self):
        from urlparse import urljoin
        from django.core.urlresolvers import reverse

        request = self.factory.get("/")

        pc = self.backend.get_processing_control(request)
        base_url = request.build_absolute_uri("/")

        self.assertEqual(pc.success_redirect_url, urljoin(base_url, self.shop.get_finished_url()))
        self.assertEqual(pc.authorize_notification_url, urljoin(base_url, reverse('%s-%s' % ("payer", "authorize",))))
        self.assertEqual(pc.settle_notification_url, urljoin(base_url, reverse('%s-%s' % ("payer", "settle",))))
        self.assertEqual(pc.redirect_back_to_shop_url, urljoin(base_url, self.shop.get_cancel_url()))

    def assertOrderDetails(self, request):
        order = self.backend.shop.get_order(request)
        order_id = self.backend.shop.get_order_unique_id(order)

        try:
            assert order
        except:
            self.fail("payer_redirect_view could not fetch order from request.")

        self.assertEqual(order_id, order_id)

        response = self.backend.payer_redirect_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response['Content-Type'])

    def test_redirect_view_with_user(self):
        request = self.factory.get("/")
        request.user = self.user

        self.assertTrue(request.user.is_authenticated())
        self.assertOrderDetails(request)

    def test_redirect_view_with_anonymous_user(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()

        setattr(request, 'session', {'order_id': self.order.id})
        self.assertEqual(request.session.get('order_id', None), self.order.id)

        self.assertFalse(request.user.is_authenticated())
        self.assertOrderDetails(request)

    def test_ip_validation(self):

        import logging
        logging.disable(logging.ERROR)

        request = self.factory.get("/")

        request.META = {'REMOTE_ADDR': self.backend.api.ip_whitelist[0]}
        self.assertTrue(self.backend.is_valid_remote_addr(request))
        request.META = {'REMOTE_ADDR': "123.234.345.456"}
        self.assertFalse(self.backend.is_valid_remote_addr(request))

        request.META = {'HTTP_X_FORWARDED_FOR': self.backend.api.ip_whitelist[0]}
        self.assertTrue(self.backend.is_valid_remote_addr(request))
        request.META = {'HTTP_X_FORWARDED_FOR': "123.234.345.456"}
        self.assertFalse(self.backend.is_valid_remote_addr(request))

        bl = ["123.234.345.456"]
        with self.settings(SHOP_PAYER_BACKEND_IP_BLACKLIST=bl):
            backend = GenericPayerBackend(shop=self.shop)

            request.META = {'REMOTE_ADDR': bl[0]}
            self.assertFalse(backend.is_valid_remote_addr(request))

        wl = ["123.234.345.456", "234.345.456.567"]
        with self.settings(SHOP_PAYER_BACKEND_IP_WHITELIST=wl, SHOP_PAYER_BACKEND_IP_BLACKLIST=bl):
            backend = GenericPayerBackend(shop=self.shop)

            request.META = {'REMOTE_ADDR': wl[0]}
            self.assertFalse(backend.is_valid_remote_addr(request))

            request.META = {'REMOTE_ADDR': bl[0]}
            self.assertFalse(backend.is_valid_remote_addr(request))

            request.META = {'REMOTE_ADDR': wl[1]}
            self.assertTrue(backend.is_valid_remote_addr(request))

    def test_valid_callback(self):
        from django.core.urlresolvers import reverse

        mock_request = self.factory.get("/")
        authorize_url = mock_request.build_absolute_uri(
            reverse(self.backend.get_url_name('authorize')) + "?order_id=%s" % self.order.id)
        settle_url = mock_request.build_absolute_uri(
            reverse(self.backend.get_url_name('settle')) + "?order_id=%s" % self.order.id)

        authorize_url_md5 = "%s&md5sum=%s" % (
            authorize_url, self.backend.api.get_checksum(authorize_url))
        settle_url_md5 = "%s&md5sum=%s" % (
            settle_url, self.backend.api.get_checksum(settle_url))

        authorize_request = self.factory.get(authorize_url_md5)
        settle_request = self.factory.get(settle_url_md5)

        self.assertTrue(self.backend.is_valid_callback(authorize_request))
        self.assertTrue(self.backend.is_valid_callback(settle_request))

        self.assertFalse(self.backend.is_valid_callback(mock_request))

    def test_callback_notification_view(self):
        from django.core.urlresolvers import reverse
        import logging
        logging.disable(logging.ERROR)

        mock_request = self.factory.get("/")
        authorize_url = mock_request.build_absolute_uri(
            reverse(self.backend.get_url_name('authorize')) + "?order_id=%s" % self.order.id)

        authorize_url_md5 = "%s&md5sum=%s" % (
            authorize_url, self.backend.api.get_checksum(authorize_url))

        authorize_request = self.factory.get(authorize_url_md5)

        authorize_request.META = authorize_request.META or {}
        authorize_request.META.update({
            'REMOTE_ADDR': self.backend.api.ip_whitelist[0],
        })

        self.assertTrue(self.backend.is_valid_remote_addr(authorize_request))
        self.assertTrue(self.backend.is_valid_callback(authorize_request))

        response = self.backend.callback_notification_view(authorize_request)
        self.assertEqual(response['Content-Type'], "text/plain")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, "TRUE")

        # Invalid md5sum
        failed_request = self.factory.get(authorize_url)
        failed_request.META = failed_request.META or {}
        failed_request.META.update({
            'REMOTE_ADDR': self.backend.api.ip_whitelist[0],
        })
        response = self.backend.callback_notification_view(failed_request)
        self.assertEqual(response['Content-Type'], "text/plain")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "FALSE")

        # Invalid REMOTE_ADDR
        failed_request = self.factory.get(authorize_url_md5)
        response = self.backend.callback_notification_view(failed_request)
        self.assertEqual(response['Content-Type'], "text/plain")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "FALSE")

    def test_handle_order_notifications(self):

        # Empty order notification
        self.backend.handle_order_notifications({})

        order = Order.objects.get(pk=self.order.id)
        self.assertEqual(order.status, Order.PROCESSING)

        # Auth notification
        data = {
            'order_id': self.order.id,
            'payer_callback_type': 'auth',
            'payer_payment_id': 'transaction_1a62c2@f27af9',
            'payment_method': 'card',
        }

        self.backend.handle_order_notifications(data)

        order = Order.objects.get(pk=self.order.id)
        self.assertEqual(order.status, Order.CONFIRMED)

        def test_cart():
            Cart.objects.get(pk=order.cart_pk)
        self.assertRaises(Cart.DoesNotExist, test_cart)

        # Settle notification
        data.update({
            'payer_callback_type': 'settle',
        })

        self.backend.handle_order_notifications(data)

        order = Order.objects.get(pk=self.order.id)
        self.assertEqual(order.status, Order.COMPLETED)
