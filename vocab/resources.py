from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from avocado.models import DataField
from restlib2.http import codes
from restlib2.resources import Resource
from preserialize.serialize import serialize
from .settings import VOCAB_FIELDS
from django.http import HttpResponse
class ItemResource(Resource):
    fields = (':pk', 'description->name', 'abbreviation', 'code', 'terminal',
        'get_absolute_url->uri', 'children', 'ancestors')

    def get(self, request, field_pk, pk):
        if not field_pk in [str(x) for x in VOCAB_FIELDS]:
            return HttpResponse(status=codes.not_found)

        try:
           field = DataField.objects.get(pk=field_pk)
           model = field.model
           item = model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return HttpResponse(status=codes.not_found)

        return serialize(item)

class ItemResourceCollection(Resource):
    search_enabled = True
    max_results = 100
    order_by = None

    def get(self, request, field_pk):
        uri = request.build_absolute_uri
        if not field_pk in [str(x) for x in VOCAB_FIELDS]:
            return HttpResponse(status=codes.not_found)

        field = DataField.objects.get(pk=field_pk)
        model = field.model

        order_by = (model.description_field,)

        # search if enabled
        # TODO removed search_enabled on field check here
        if request.GET.has_key('q'):
            kwargs = {}
            q = request.GET['q']
            query = Q()

            for field in getattr(model, 'search_fields', ()):
                query = query | Q(**{'%s__icontains' % field: q})

            results = serialize(model.objects.filter(query).order_by('-parent', *order_by)[:self.max_results])
            for node in results:
                node['uri'] = uri(reverse("vocab:value", kwargs={"field_pk" : field_pk, "pk": node['id']}))

            return results

        # if no nodes have children, we return not found so the client
        # can react (go into search only mode)
        if model.objects.filter(children__isnull = False).count() == 0:
            return HttpResponse(status=codes.not_found)
        # get all root items by default
        return serialize(model.objects.filter(parent=None).order_by(*order_by))

class Resources(Resource):
    def get(self, request, field_pk):
        uri = request.build_absolute_uri
        return {
            "_links": {
               "items": {
                    "href": uri(reverse("vocab:root",
                        kwargs={'field_pk':field_pk})) + "values/",
                    "rel": "items"
               },
               "directory": {
                   "href": uri(reverse("vocab:root",
                       kwargs={'field_pk':field_pk})) + "directory/",
                   "rel": "directory"
               },
               "search": {
                   "href": uri(reverse("vocab:root",
                       kwargs={'field_pk':field_pk})) + "search/",
                   "rel": "search"
               }
            },
            "title": "Serrano Vocab Browser Hypermedia API",
        }
