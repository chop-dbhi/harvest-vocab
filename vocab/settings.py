from django.conf import settings

VOCAB_FIELDS = getattr(settings, 'VOCAB_FIELDS', ())
