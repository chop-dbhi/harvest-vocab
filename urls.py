from django.conf.urls.defaults import *
from django.conf import settings
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
urlpatterns = patterns('production.views',
    url(r'^$', 'vocab_browser', name='vocab-browser-top'),
    url(r'^search', 'vocabulary.vocab_search', name='vocab-search'),
    url(r'^autocomplete$', 'vocabulary.vocab_autocomplete', name='vocab-autocomplete'),
    url(r'^simple/$', 'vocabulary.vocab_browser', name='vocab-browser-top'),
    url(r'^simple/(?P<category>\d+)/$', 'vocabulary.vocab_browser', name='vocab-browser-cat'),
    
    url(r'^browse/$', 'vocabulary.vocab_browser_json', name='ajax-browser-top'),
    url(r'^browse/(?P<category>\d+)/$', 'vocabulary.vocab_browser_json', name='ajax-browser-cat'),
    url(r'^json$','vocabulary.vocab_json'),
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