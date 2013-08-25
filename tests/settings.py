DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'vocab.db',
    },
    'alt': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'alt.db',
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'vocab',
    'tests',
    'avocado'
)

MODELTREES = {
    'default': {
        'model': "tests.ticket",
    }
}

SECRET_KEY = 'abc123'
