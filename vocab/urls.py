from django.conf.urls.defaults import url, patterns, include
from .settings import VOCAB_FIELDS

override_fields = '|'.join([str(f) for f in VOCAB_FIELDS])

urlpatterns = patterns('',
    url(r'', include(patterns('',
        url(r'^fields/(?P<pk>{0})/values/$'.format(override_fields),
            'vocab.resources.ItemsResource', name='items'),
       url(r'^fields/(?P<pk>{0})/values/(?P<item_pk>\d+)/$'.format(override_fields),
           'vocab.resources.ItemResource', name='item'),
       url(r'^fields/(?P<pk>{0})/values/(?P<item_pk>\d+)/values/$'.format(override_fields),
           'vocab.resources.ItemsResource', name='items'),
    ), namespace='vocab'))
)
