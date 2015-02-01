from django.test import TestCase
from decimal import Decimal
from helper import buyer_details_from_user

from shop.models.ordermodel import Order
from shop.models import AddressModel
from django.contrib.auth.models import AnonymousUser
from helper import populate_buyer_details_dict
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User


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

        with self.settings(SHOP_PAYER_BACKEND_ADDRESS_HANDLER='django_shop_payer_backend.tests.override_address'):
            buyer = buyer_details_from_user(AnonymousUser(), self.order)

            self.assertEquals(buyer.first_name, "Peter")
            self.assertEquals(buyer.last_name, "Parker")
            self.assertEquals(buyer.address_line_1, "Back Street 987")
            self.assertEquals(buyer.postal_code, "98765")
            self.assertEquals(buyer.city, "Somewhere")
            self.assertEquals(buyer.email, None)

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


def override_address(*args, **kwargs):
    address = AddressModel.objects.create(
        name="Peter Parker",
        address="Back Street 987",
        zip_code="98765",
        city="Somewhere",
        state="N/A",
    )
    return address
