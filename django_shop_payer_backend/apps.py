from django.apps import AppConfig
from django.utils.translation import ugettext, ugettext_lazy as _


class DjangoShopPayerBackend(AppConfig):
    name = 'django_shop_payer_backend'
    verbose_name = _("Django Shop Payer Backend")
