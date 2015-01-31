from django.test import TestCase


class HelpersTestCase(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_address_extraction(self):

        self.assertTrue(True)

        # Anonymous user, no callbacks (vanilla)
        # Logged in user, no callbacks
        # Anonoymous user, callbacks
        # Logged in user, callbacks

        # from helpers import buyer_details_from_user

        # user = None
        # order = None

        # buyer_details_from_user(user=user, order=order)
