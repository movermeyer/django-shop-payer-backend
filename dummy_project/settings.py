DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
    }
}
USE_TZ = False
SITE_ID = 1
SECRET_KEY = 'abcde12345'

ROOT_URLCONF = 'dummy_project.urls'
STATIC_URL = '/static/'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'polymorphic',
    'shop',
    'shop.addressmodel',
    'django_shop_payer_backend',
)

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

SHOP_PAYER_BACKEND_AGENT_ID = "AGENT_ID"
SHOP_PAYER_BACKEND_ID1 = "6866ef97a972ba3a2c6ff8bb2812981054770162"
SHOP_PAYER_BACKEND_ID2 = "1388ac756f07b0dda2961436ba8596c7b7995e94"
