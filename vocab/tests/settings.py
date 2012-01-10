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
    'vocab',
    'vocab.tests',
)
