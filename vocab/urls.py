from django.conf.urls.defaults import *
from django.conf import settings
from vocab.views import children_of_folder, search_nodes, retrieve_node
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
urlpatterns = patterns('',
    url(r'^browse/(?P<folder_id>\d+)?$', children_of_folder),
    url(r'^search', search_nodes),
    url(r'', retrieve_node)
)
