#!/bin/sh

PYTHONPATH=. DJANGO_SETTINGS_MODULE='vocab.tests.settings' `which django-admin.py` test vocab
