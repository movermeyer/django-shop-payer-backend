VERSION = '0.1.3'

default_app_config = 'django_shop_payer_backend.apps.DjangoShopPayerBackend'

try:
    from django.core.checks import register, Info
    from django.conf import settings

    @register()
    def check_payment_backend_settings(app_configs, **kwargs):
        errors = []
        backends = getattr(settings, 'SHOP_PAYMENT_BACKENDS', [])

        agent_key = "SHOP_PAYER_BACKEND_AGENT_ID"
        key_1_key = "SHOP_PAYER_BACKEND_ID1"
        key_2_key = "SHOP_PAYER_BACKEND_ID2"

        if any(item.startswith('django_shop_payer_backend.backends.') for item in backends):

            if not hasattr(settings, agent_key) or not getattr(settings, agent_key, None):
                errors.append(Info(
                    'Payer Agent ID not in settings.',
                    hint='Add a setting value for the key `%s` containing the Agent ID for the Payer API.' % agent_key,
                    obj=__name__,
                    id='django_shop_payer_backend.E001',
                ))

            if not hasattr(settings, key_1_key) or not getattr(settings, key_1_key, None):
                errors.append(Info(
                    'Payer Key 1 not in settings.',
                    hint='Add a setting value for the key `%s` containing the Key 1 for the Payer API.' % key_1_key,
                    obj=__name__,
                    id='django_shop_payer_backend.E002',
                ))

            if not hasattr(settings, key_2_key) or not getattr(settings, key_2_key, None):
                errors.append(Info(
                    'Payer Key 2 not in settings.',
                    hint='Add a setting value for the key `%s` containing the Key 2 for the Payer API.' % key_2_key,
                    obj=__name__,
                    id='django_shop_payer_backend.E003',
                ))

        return errors

except Exception:
    pass
