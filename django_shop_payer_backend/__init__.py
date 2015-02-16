VERSION = '0.1.7'

default_app_config = 'django_shop_payer_backend.apps.DjangoShopPayerBackend'


def check_config(settings):
    backends = getattr(settings, 'SHOP_PAYMENT_BACKENDS', [])

    agent_key = "SHOP_PAYER_BACKEND_AGENT_ID"
    key_1_key = "SHOP_PAYER_BACKEND_ID1"
    key_2_key = "SHOP_PAYER_BACKEND_ID2"

    errors = []

    if any(item.startswith('django_shop_payer_backend.backends.') for item in backends):

        if not hasattr(settings, agent_key) or not getattr(settings, agent_key, None):
            errors.append({
                'msg': 'Payer Agent ID not in settings.',
                'hint': 'Add a setting value for the key `%s` containing the Agent ID for the Payer API.' % agent_key,
                'obj': __name__,
                'id': 'django_shop_payer_backend.E001',
            })

        if not hasattr(settings, key_1_key) or not getattr(settings, key_1_key, None):
            errors.append({
                'msg': 'Payer Key 1 not in settings.',
                'hint': 'Add a setting value for the key `%s` containing the Key 1 for the Payer API.' % key_1_key,
                'obj': __name__,
                'id': 'django_shop_payer_backend.E002',
            })

        if not hasattr(settings, key_2_key) or not getattr(settings, key_2_key, None):
            errors.append({
                'msg': 'Payer Key 2 not in settings.',
                'hint': 'Add a setting value for the key `%s` containing the Key 2 for the Payer API.' % key_2_key,
                'obj': __name__,
                'id': 'django_shop_payer_backend.E003',
            })

    return errors


try:
    from django.core.checks import register, Info

    @register()
    def check_payment_backend_settings(app_configs, **kwargs):
        from django.conf import settings
        errors = []

        config_errors = check_config(settings)
        for error in config_errors:
            errors.append(Info(**error))

        return errors
except:
    pass
