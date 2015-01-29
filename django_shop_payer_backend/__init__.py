VERSION = '0.1'

default_app_config = 'django_shop_payer_backend.apps.DjangoShopPayerBackend'

try:
    from django.core.checks import register
    from django.core.checks import Error, Info

    from django.utils.translation import ugettext as _
    from django.conf import settings

    @register()
    def check_payment_backend_settings(app_configs, **kwargs):
        errors = []

        if any(item.startswith('django_shop_payer_backend.backends.') for item in getattr(settings, 'SHOP_PAYMENT_BACKENDS', [])):

            if not hasattr(settings, 'SHOP_PAYMENT_BACKEND_PAYER_AGENT_ID') or not getattr(settings, 'SHOP_PAYMENT_BACKEND_PAYER_AGENT_ID', None):
                errors.append(Info(
                    _('Payer Agent ID not in settings.'),
                    hint=_('Add a setting property for the key `SHOP_PAYMENT_BACKEND_PAYER_AGENT_ID` containing the Agent ID for the Payer API.'),
                    obj=__name__,
                    id='django_shop_payer_backend.E001',
                ))

            if not hasattr(settings, 'SHOP_PAYMENT_BACKEND_PAYER_ID1') or not getattr(settings, 'SHOP_PAYMENT_BACKEND_PAYER_ID1', None):
                errors.append(Info(
                    _('Payer Key 1 not in settings.'),
                    hint=_('Add a setting property for the key `SHOP_PAYMENT_BACKEND_PAYER_ID1` containing the Key 1 for the Payer API.'),
                    obj=__name__,
                    id='django_shop_payer_backend.E002',
                ))

            if not hasattr(settings, 'SHOP_PAYMENT_BACKEND_PAYER_ID2') or not getattr(settings, 'SHOP_PAYMENT_BACKEND_PAYER_ID2', None):
                errors.append(Info(
                    _('Payer Key 2 not in settings.'),
                    hint=_('Add a setting property for the key `SHOP_PAYMENT_BACKEND_PAYER_ID2` containing the Key 2 for the Payer API.'),
                    obj=__name__,
                    id='django_shop_payer_backend.E003',
                ))


        return errors

except Exception, e:
    pass
