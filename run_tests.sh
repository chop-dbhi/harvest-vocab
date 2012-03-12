#!/bin/sh

PYTHONPATH=. DJANGO_SETTINGS_MODULE='vocab.tests.settings' coverage run ../bin/django-admin.py test vocab
coverage html
