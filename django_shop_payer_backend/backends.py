# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from shop.payment.backends.prepayment import ForwardFundBackend
from django.conf.urls import patterns, url
from django.conf import settings
from django.core.urlresolvers import reverse

from decimal import Decimal
from django.utils import timezone
from django.conf.urls import patterns, url
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response
from shop.models.ordermodel import Order, OrderPayment
from shop.models.cartmodel import Cart
from shop.util.decorators import on_method, order_required
from shop.order_signals import confirmed

from helper import payer_order_item_from_order_item, buyer_details_from_user
from payer_api.postapi import PayerPostAPI
from payer_api.order import (
    PayerProcessingControl,
    PayerBuyerDetails,
    PayerOrderItem,
    PayerOrder,
)

from payer_api import DEBUG_MODE_SILENT
from django.contrib.sites.shortcuts import get_current_site
from forms import PayerRedirectForm
import abc



class BasePayerBackend(object):
    __metaclass__  = abc.ABCMeta

    url_namespace = 'payer'
    backend_name = _('Advance payment')
    template = 'payer_backend/redirect.html'

    def __init__(self, shop):
        self.shop = shop

        self.api = PayerPostAPI(
            agent_id=getattr(settings, 'SHOP_PAYMENT_BACKEND_PAYER_AGENT_ID', ''),
            key_1=getattr(settings, 'SHOP_PAYMENT_BACKEND_PAYER_ID1', ''),
            key_2=getattr(settings, 'SHOP_PAYMENT_BACKEND_PAYER_ID2', ''),
            debug_mode=getattr(settings, 'SHOP_PAYMENT_BACKEND_DEBUG_MODE', DEBUG_MODE_SILENT),
            test_mode=getattr(settings, 'SHOP_PAYMENT_BACKEND_TEST_MODE', False),
        )


    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.payer_redirect_view, name='payer-redirect'),
        )
        return urlpatterns


    def build_absolute_url(self, request, path):
        url_scheme = 'https' if request.is_secure() else 'http'
        url_domain = get_current_site(request).domain

        return '%s://%s%s' % (url_scheme, url_domain, path,)

    def get_processing_control(self, request):

        return PayerProcessingControl(
            success_redirect_url=self.build_absolute_url(request, "/webshop/success/"),
            authorize_notification_url=self.build_absolute_url(request, "/webshop/auth/"),
            settle_notification_url=self.build_absolute_url(request, "/webshop/settle/"),
            redirect_back_to_shop_url=self.build_absolute_url(request, reverse('shop_welcome')),
        )

    # @on_method(shop_login_required)
    @on_method(order_required)
    def payer_redirect_view(self, request):
        """
        This simple view does nothing but record the "payment" as being
        complete since we trust the delivery guy to collect money, and redirect
        to the success page. This is the most simple case.
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

        for info in order.extra_info.all():
            payer_order.add_info_line(info.text())

        self.api.set_processing_control(self.get_processing_control(request))
        self.api.set_order(payer_order)

        redirect_data = self.api.get_post_data()
        form = PayerRedirectForm(redirect_data=redirect_data)

        xml_data = self.api.get_xml_data(pretty_print=True)


        context = RequestContext(request, {
            'order': order,
            'redirect_data': redirect_data,
            'form_action': self.api.get_post_url(),
            'form': form,
            'xml_data': xml_data,
        })

        return render_to_response(self.template, context)

    # @on_method(shop_login_required)
    # @on_method(order_required)
    # def payment_completed():
    #     order = self.shop.get_order(request)

    #     self.shop.confirm_payment(
    #         order, self.shop.get_order_total(order), "None",
    #         self.backend_name)

    #     return HttpResponseRedirect(self.shop.get_finished_url())


    # def _create_confirmed_order(self, order, transaction_id):
    #     """
    #     Create an order from the current cart but does not mark it as payed.
    #     Instead mark the order as CONFIRMED only, as somebody manually has to
    #     check bank account statements and mark the payments.
    #     """
    #     OrderPayment.objects.create(order=order, amount=Decimal(0),
    #         transaction_id=transaction_id, payment_method=self.backend_name)

    #     # Confirm the current order
    #     order.status = Order.CONFIRMED
    #     order.save()

    #     # empty the related cart
    #     try:
    #         cart = Cart.objects.get(pk=order.cart_pk)
    #         cart.empty()
    #     except Cart.DoesNotExist:
    #         pass
    #     confirmed.send(sender=self, order=order)




class PayerCreditCardPaymentBackend(BasePayerBackend):

    url_namespace = 'payer-redirect'
    backend_name = _('Credit card')

    # def get_urls(self):
    #     urlpatterns = patterns('',
    #         url(r'^$', self.advance_payment_view, name='payer-creditcard'),
    #     )
    #     return urlpatterns


class PayerBankPaymentBackend(BasePayerBackend):

    url_namespace = 'payer-redirect'
    backend_name = _('Bank payment')

    # def get_urls(self):
    #     urlpatterns = patterns('',
    #         url(r'^$', self.advance_payment_view, name='payer-bankpayment'),
    #     )
    #     return urlpatterns


class PayerPhonePaymentBackend(object):

    def __init__(self):
        raise NotImplementedError("Not implemented yet")


class PayerInvoicePaymentBackend(object):

    def __init__(self):
        raise NotImplementedError("Not implemented yet")
