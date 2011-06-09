DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'vocab.db',
    }
}

INSTALLED_APPS = (
    'vocab',
    'vocab.tests',
)
