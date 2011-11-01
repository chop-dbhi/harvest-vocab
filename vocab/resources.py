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
    max_results = 100
    order_by = None

    def GET(self, request):
        queryset = self.queryset(request)

        order_by = self.order_by
        if not order_by:
            order_by = (queryset.model.description_field,)

        # search if enabled
        if self.search_enabled and request.GET.has_key('q'):
            kwargs = {}
            q = request.GET['q']
            query = Q()

            for field in getattr(self.model, 'search_fields', ()):
                query = query | Q(**{'%s__icontains' % field: q})

            queryset = queryset.order_by('-parent', *order_by)

            return queryset.filter(query)[:self.max_results]

        # get all root items by default
        return queryset.filter(parent=None).order_by(*order_by)

