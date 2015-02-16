# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import patterns, url
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
import logging

from django.template import RequestContext
from django.shortcuts import render_to_response
from shop.models.ordermodel import Order
from shop.models.cartmodel import Cart
from shop.util.decorators import on_method, order_required, shop_login_required
from shop.order_signals import confirmed, completed

from forms import PayerRedirectForm
from helper import (
    payer_order_item_from_order_item,
    buyer_details_from_user,
    payer_order_item_from_extra_order_price,
    string_chunks,
)
from payer_api.postapi import PayerPostAPI
from payer_api.xml import PayerXMLDocument
from payer_api.order import PayerProcessingControl, PayerOrder

from payer_api import (
    DEBUG_MODE_SILENT,
    PAYMENT_METHOD_CARD,
    PAYMENT_METHOD_BANK,
    PAYMENT_METHOD_PHONE,
    PAYMENT_METHOD_INVOICE,
)


logger = logging.getLogger('django.request')


class GenericPayerBackend(object):

    url_namespace = 'payer'
    backend_name = _('Payer')
    template = 'payer_backend/redirect.html'
    payment_methods = [
        PAYMENT_METHOD_CARD,
        PAYMENT_METHOD_BANK,
        PAYMENT_METHOD_PHONE,
        PAYMENT_METHOD_INVOICE,
    ]

    def __init__(self, shop):
        self.shop = shop

        self.api = PayerPostAPI(
            agent_id=getattr(settings, 'SHOP_PAYER_BACKEND_AGENT_ID', ''),
            key_1=getattr(settings, 'SHOP_PAYER_BACKEND_ID1', ''),
            key_2=getattr(settings, 'SHOP_PAYER_BACKEND_ID2', ''),
            payment_methods=self.payment_methods,
            test_mode=getattr(settings, 'SHOP_PAYER_BACKEND_TEST_MODE', False),
            debug_mode=getattr(settings, 'SHOP_PAYER_BACKEND_DEBUG_MODE', DEBUG_MODE_SILENT),
            hide_details=getattr(settings, 'SHOP_PAYER_BACKEND_HIDE_DETAILS', False),
        )

        for ip in getattr(settings, 'SHOP_PAYER_BACKEND_IP_WHITELIST', []):
            self.api.add_whitelist_ip(ip)

        for ip in getattr(settings, 'SHOP_PAYER_BACKEND_IP_BLACKLIST', []):
            self.api.add_blacklist_ip(ip)

    def get_url_name(self, name=None):
        if not name:
            return self.url_namespace
        return '%s-%s' % (self.url_namespace, name,)

    def get_urls(self):
        urlpatterns = patterns(
            '',
            url(r'^$', self.payer_redirect_view, name=self.get_url_name()),
            url(r'^authorize/$', self.callback_notification_view, name=self.get_url_name('authorize')),
            url(r'^settle/$', self.callback_notification_view, name=self.get_url_name('settle')),
        )
        return urlpatterns

    def get_processing_control(self, request):

        return PayerProcessingControl(
            success_redirect_url=request.build_absolute_uri(self.shop.get_finished_url()),
            authorize_notification_url=request.build_absolute_uri(reverse(self.get_url_name('authorize'))),
            settle_notification_url=request.build_absolute_uri(reverse(self.get_url_name('settle'))),
            redirect_back_to_shop_url=request.build_absolute_uri(self.shop.get_cancel_url()),
        )

    @on_method(shop_login_required)
    @on_method(order_required)
    def payer_redirect_view(self, request):
        """
        This view generates the order XML data and other key-value pairs needed,
        outputs the as hidden input elemens in a form and redirects to Payer.
        """

        order = self.shop.get_order(request)
        description = self.shop.get_order_short_name(order)
        order_id = self.shop.get_order_unique_id(order)

        user = None
        if request.user.is_authenticated():
            user = request.user

        payer_order = PayerOrder(
            order_id=order_id,
            description=description,
        )
        payer_order.set_buyer_details(buyer_details_from_user(user=user, order=order))

        for order_item in order.items.all():
            payer_order.add_order_item(payer_order_item_from_order_item(order_item))

        for extra_order_price in order.extraorderpricefield_set.all():
            payer_order.add_order_item(payer_order_item_from_extra_order_price(extra_order_price))

        for info in order.extra_info.all():
            for t in list(string_chunks(info.text, 255)):
                payer_order.add_info_line(t)

        self.api.set_processing_control(self.get_processing_control(request))
        self.api.set_order(payer_order)

        redirect_data = self.api.get_post_data()
        form = PayerRedirectForm(redirect_data=redirect_data)

        ctx_data = {
            'order': order,
            'redirect_data': redirect_data,
            'form_action': self.api.get_post_url(),
            'form': form,
        }

        if settings.DEBUG:
            ctx_data['xml_data'] = self.api.get_xml_data(pretty_print=True)

        context = RequestContext(request, ctx_data)

        return render_to_response(self.template, context)

    def is_valid_remote_addr(self, request):
        def get_remote_addr(request):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip

        try:
            remote_addr = get_remote_addr(request)

            return self.api.validate_callback_ip(remote_addr)
        except Exception as e:
            logging.error(u"IP address callback did not validate: %s" % unicode(e))

        return False

    def is_valid_callback(self, request):

        try:
            url = request.build_absolute_uri(request.get_full_path())
            return self.api.validate_callback_url(url)
        except Exception as e:
            logging.error(u"Callback URL did not validate: %s" % unicode(e))

        return False

    def callback_notification_view(self, request):
        valid_callback = self.is_valid_remote_addr(request) and self.is_valid_callback(request)

        if valid_callback:
            try:
                self.handle_order_notifications(request.GET)
            except Exception as e:
                logging.error(u"Error handling order notification: %s" % unicode(e))

        return HttpResponse("TRUE" if valid_callback else "FALSE", content_type="text/plain")

    def handle_order_notifications(self, data):

        order_id = data.get(PayerXMLDocument.ORDER_ID_URL_PARAMETER_NAME,
                            data.get('payer_merchant_reference_id', None))
        payment_method = data.get('payer_payment_type', 'unknown')
        transaction_id = data.get('payer_payment_id', data.get('payread_payment_id', None))
        callback_type = data.get('payer_callback_type', '').lower()
        # testmode = bool(data.get('payer_testmode', 'false') == 'true')
        # added_fee = data.get('payer_added_fee', 0)

        if order_id is not None:

            order = Order.objects.get(pk=order_id)

            if callback_type == 'auth':

                # Payment approved, update order status, empty cart
                order.status = Order.CONFIRMED
                order.save()

                try:
                    cart = Cart.objects.get(pk=order.cart_pk)
                    cart.empty()
                except Cart.DoesNotExist:
                    pass

                confirmed.send(sender=self, order=order)

            elif callback_type == 'settle':

                # Payment completed, update order status, add payment
                order.status = Order.COMPLETED

                self.shop.confirm_payment(order, self.shop.get_order_total(order), transaction_id,
                                          u"Payer %s (%s)" % (unicode(self.backend_name).lower(), payment_method,))

                completed.send(sender=self, order=order)


class PayerCreditCardPaymentBackend(GenericPayerBackend):

    url_namespace = 'payer-card'
    backend_name = _('Credit card')
    payment_methods = [
        PAYMENT_METHOD_CARD,
    ]


class PayerBankPaymentBackend(GenericPayerBackend):

    url_namespace = 'payer-bank'
    backend_name = _('Bank payment')
    payment_methods = [
        PAYMENT_METHOD_BANK,
    ]


class PayerPhonePaymentBackend(GenericPayerBackend):

    url_namespace = 'payer-phone'
    backend_name = _('Phone payment')
    payment_methods = [
        PAYMENT_METHOD_PHONE,
    ]


class PayerInvoicePaymentBackend(GenericPayerBackend):

    url_namespace = 'payer-invoice'
    backend_name = _('Invoice')
    payment_methods = [
        PAYMENT_METHOD_INVOICE,
    ]
