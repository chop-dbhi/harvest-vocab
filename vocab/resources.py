from django.db.models import Q
from avocado.models import DataField
from django.conf import settings
from restlib2.http import codes
from restlib2 import resource

class ItemResource(resource):
    fields = (':pk', 'description->name', 'abbreviation', 'code', 'terminal',
        'get_absolute_url->uri', 'children', 'ancestors')

    def get(self, request, field_pk, pk):
        if not field_pk in [str(x) for x in settings.VOCAB_FIELDS]:
            return codes.NOT_FOUND

        field = DataField.objects.get(pk=field_pk)
        model = field.model

        item = model.objects.get(request, pk=pk)

        if item is None:
            return codes.NOT_FOUND
        return item

class ItemResourceCollection(resource):
    search_enabled = True
    max_results = 100
    order_by = None

    def get(self, request, field_pk):
        if not field_pk in [str(x) for x in settings.VOCAB_FIELDS]:
            return codes.NOT_FOUND

        field = DataField.objects.get(pk=field_pk)
        model = field.model

        order_by = (model.description_field,)

        # search if enabled
        if field.search_enabled and request.GET.has_key('q'):
            kwargs = {}
            q = request.GET['q']
            query = Q()

            for field in getattr(model, 'search_fields', ()):
                query = query | Q(**{'%s__icontains' % field: q})

            queryset = queryset.order_by('-parent', *order_by)

            return model.objects.filter(query)[:self.max_results] \
                .order_by('-parent', *order_by)

        # get all root items by default
        return model.objects.filter(parent=None).order_by(*order_by)

class Resources(resource):
    pass

