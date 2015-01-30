from distutils.core import setup

VERSION = __import__("django_shop_payer_backend").VERSION

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Topic :: Software Development',
]

install_requires = [
    'django-shop>=0.2.0',
    'python-payer-api>=0.1.0',
]

setup(
    name="django-shop-payer-backend",
    description="Payment backend for django SHOP and Payer.",
    version=VERSION,
    author="Simon Fransson",
    author_email="simon@dessibelle.se",
    url="https://github.com/dessibelle/django-shop-payer-backend",
    download_url="https://github.com/dessibelle/django-shop-payer-backend/archive/%s.tar.gz" % VERSION,
    packages=['django_shop_payer_backend'],
    install_requires=install_requires,
    classifiers=CLASSIFIERS,
    license="MIT",
)
