VERSION = '0.1.0'

default_app_config = 'django_shop_payer_backend.apps.DjangoShopPayerBackend'

try:
    from django.core.checks import register
    from django.core.checks import Error, Info

    from django.conf import settings

    @register()
    def check_payment_backend_settings(app_configs, **kwargs):
        errors = []

        if any(item.startswith('django_shop_payer_backend.backends.') for item in getattr(settings, 'SHOP_PAYMENT_BACKENDS', [])):

            if not hasattr(settings, 'SHOP_PAYER_BACKEND_AGENT_ID') or not getattr(settings, 'SHOP_PAYER_BACKEND_AGENT_ID', None):
                errors.append(Info(
                    'Payer Agent ID not in settings.',
                    hint='Add a setting property for the key `SHOP_PAYER_BACKEND_AGENT_ID` containing the Agent ID for the Payer API.',
                    obj=__name__,
                    id='django_shop_payer_backend.E001',
                ))

            if not hasattr(settings, 'SHOP_PAYER_BACKEND_ID1') or not getattr(settings, 'SHOP_PAYER_BACKEND_ID1', None):
                errors.append(Info(
                    'Payer Key 1 not in settings.',
                    hint='Add a setting property for the key `SHOP_PAYER_BACKEND_ID1` containing the Key 1 for the Payer API.',
                    obj=__name__,
                    id='django_shop_payer_backend.E002',
                ))

            if not hasattr(settings, 'SHOP_PAYER_BACKEND_ID2') or not getattr(settings, 'SHOP_PAYER_BACKEND_ID2', None):
                errors.append(Info(
                    'Payer Key 2 not in settings.',
                    hint='Add a setting property for the key `SHOP_PAYER_BACKEND_ID2` containing the Key 2 for the Payer API.',
                    obj=__name__,
                    id='django_shop_payer_backend.E003',
                ))


        return errors

except Exception, e:
    pass
