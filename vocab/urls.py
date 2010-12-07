from django.conf.urls.defaults import *
from django.conf import settings
from vocab.views import children_of_folder, dependencies, search_nodes, retrieve_node
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
urlpatterns = patterns('',
    url(r'^dependencies', dependencies),
    url(r'^browse/(?P<folder_id>\d+)?$', children_of_folder),
    url(r'^search', search_nodes),
    url(r'', retrieve_node)
)

if settings.DEBUG:
    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]
    urlpatterns += patterns('',
        url(r'^%s(?P<path>.*)$' % _media_url, 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
    del _media_url
