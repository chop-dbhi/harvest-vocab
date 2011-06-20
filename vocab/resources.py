from django.db.models import Q
from restlib import resources, http

class ItemResource(resources.Resource):
    def GET(self, request, pk):
        item = self.get(request, pk=pk)

        if item is None:
            return http.NOT_FOUND

        return item


class ItemResourceCollection(resources.Resource):
    search_enabled = True

    def GET(self, request):
        queryset = self.queryset(request)

        # search if enabled
        if request.GET.has_key('q') and self.search_enabled:
            kwargs = {}
            q = request.GET['q']
            query = Q()

            for field in getattr(self.model, 'search_fields', ()):
                query = query | Q(**{'%s__icontains' % field: q})

            return queryset.filter(query)

        # get all root items
        return queryset.filter(parent=None).order_by('name')

