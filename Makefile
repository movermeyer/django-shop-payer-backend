.PHONY: flake8 test coverage

flake8:
	flake8 --ignore=W999 django_shop_payer_backend

test:
	DJANGO_SETTINGS_MODULE=dummy_project.settings PYTHONPATH=. django-admin.py test

coverage:
	coverage erase
	DJANGO_SETTINGS_MODULE=dummy_project.settings PYTHONPATH=. \
		coverage run --branch --source=django_shop_payer_backend \
		`which django-admin.py` test
	coverage combine
	coverage html
	coverage report
