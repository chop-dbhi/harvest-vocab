from django.conf.urls.defaults import url, patterns, include
from django.conf import settings

override_fields = '|'.join([str(f) for f in settings.VOCAB_FIELDS])

urlpatterns = patterns('',
    url(r'^fields/(?P<field_pk>{0})/values/(?P<pk>\d)'.format(override_fields), 'vocab.resources.ItemResource')
)
