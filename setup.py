from distutils.core import setup
import setuptools
import os
VERSION = __import__("django_shop_payer_backend").VERSION

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Topic :: Software Development',
]

install_requires = [
    'Django>=1.4',
    'django-shop>=0.2.0',
    'python-payer-api>=0.1.2',
]


def read_md(path):
    long_desc = ""
    if os.path.exists(path):
        try:
            from pypandoc import convert
            long_desc = convert(path, 'rst')
        except:
            try:
                long_desc = open(path, 'r').read()
            except:
                pass
    return long_desc

long_desc = read_md("README.md")

setup(
    name="django-shop-payer-backend",
    description="Payment backend for django SHOP and Payer.",
    long_description=long_desc,
    version=VERSION,
    author="Simon Fransson",
    author_email="simon@dessibelle.se",
    url="https://github.com/dessibelle/django-shop-payer-backend",
    download_url="https://github.com/dessibelle/django-shop-payer-backend/archive/%s.tar.gz" % VERSION,
    packages=setuptools.find_packages(exclude=['dummy_project']),  # ['django_shop_payer_backend'],
    include_package_data=True,
    # package_data={'django_shop_payer_backend': [
    #     'locale/*/*/*',
    #     'templates/*/*',
    # ]},
    install_requires=install_requires,
    classifiers=CLASSIFIERS,
    license="MIT",
)
