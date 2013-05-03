from django.conf.urls.defaults import url, patterns, include
from django.conf import settings

override_fields = '|'.join([str(f) for f in settings.VOCAB_FIELDS])

urlpatterns = patterns('', 
    url(r'', include(patterns('',
       url(r'^fields/(?P<field_pk>{0})/values/(?P<pk>\d+)/$'.format(override_fields), 'vocab.resources.ItemResource', 
           name="value"),
       url(r'^fields/(?P<field_pk>{0})/directory/$'.format(override_fields), 'vocab.resources.ItemResourceCollection'),
       url(r'^fields/(?P<field_pk>{0})/search/$'.format(override_fields), 'vocab.resources.ItemResourceCollection'),
       url(r'^fields/(?P<field_pk>{0})/$'.format(override_fields), 'vocab.resources.Resources', 
           name='root')
    ), namespace="vocab"))
)
