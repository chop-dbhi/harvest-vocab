import functools
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from avocado.models import DataField
from avocado.events import usage
from restlib2.resources import Resource
from serrano.resources.field.values import FieldValues
from preserialize.serialize import serialize
from .settings import VOCAB_FIELDS


def item_posthook(instance, data, request, pk):
    "Post-serialize hook for item instances."
    uri = request.build_absolute_uri

    data.update({
        'label': unicode(instance),
        'value': instance.pk,
    })

    parent_kwargs = {'pk': pk}
    if instance.parent_id:
        parent_kwargs['item_pk'] = instance.parent_id

    # Add link to self and parent
    data['_links'] = {
        'self': {
            'href': uri(reverse('vocab:item', kwargs={
                'pk': pk,
                'item_pk': data['id'],
            }))
        },
        'parent': {
            'href': uri(reverse('vocab:items', kwargs=parent_kwargs))
        }
    }

    # If this item is not a terminal, add link to child nodes
    if not instance.terminal:
        data['_links']['children'] = {
            'href': uri(reverse('vocab:items', kwargs={
                'pk': pk,
                'item_pk': data['id'],
            }))
        }

    return data


class ItemBaseResource(Resource):
    def is_not_found(self, request, response, pk, item_pk=None):
        # Non-integer value
        try:
            pk = int(pk)
        except (ValueError, TypeError):
            return True

        # Field does not exist
        try:
            field = DataField.objects.get(pk=pk)
        except DataField.DoesNotExist:
            return True

        # If an item is specified, ensure it exists
        if item_pk:
            try:
                request.item = field.model.objects.get(pk=item_pk)
            except field.model.DoesNotExist:
                return True

        # Attach to request for downstream use
        request.instance = field

    def prepare(self, request, objects, pk, template=None):
        if template is None:
            template = {'fields': [':pk']}
        posthook = functools.partial(item_posthook, request=request, pk=pk)
        return serialize(objects, posthook=posthook, **template)



# TODO if/when serrano becomes more reusable, update and remove boilerplate code
class ItemsResource(ItemBaseResource, FieldValues):
    """Resource for vocab items. If no item is specified, items without a
    parent are returned, otherwise the children of the specified item are
    returned.

    This is a modified form of serrano.resources.FieldValues.
    """

    template = None

    def get_base_values(self, request, instance, params, item_pk=None):
        queryset = super(ItemsResource, self).get_base_values(request, instance, params)
        queryset = queryset.filter(parent__pk=item_pk)
        return queryset

    def get_all_values(self, request, instance, params, item_pk=None):
        queryset = self.get_base_values(request, instance, params, item_pk)
        return self.prepare(request, queryset, instance.pk)

    def get_search_values(self, request, instance, params, item_pk=None):
        queryset = self.get_base_values(request, instance, params, item_pk)
        condition = Q()
        for field in instance.model.search_fields:
            condition = condition | Q(**{'{0}__icontains'.format(field): params['query']})
        queryset = queryset.filter(condition)
        return self.prepare(request, queryset, instance.pk)

    def get_random_values(self, request, instance, params, item_pk=None):
        queryset = self.get_base_values(request, instance, params, item_pk)
        queryset = queryset.order_by('?')[:params['random']]
        return self.prepare(request, queryset, instance.pk)

    def get(self, request, pk, item_pk=None):
        instance = request.instance
        params = self.get_params(request)

        if params['random']:
            return self.get_random_values(request, instance, params, item_pk)

        page = params['page']
        per_page = params['per_page']

        # If a query term is supplied, perform the icontains search
        if params['query']:
            usage.log('values', instance=instance, request=request, data={
                'query': params['query'],
                'item_pk': item_pk,
            })
            values = self.get_search_values(request, instance, params, item_pk)
        else:
            values = self.get_all_values(request, instance, params, item_pk)

        # No page specified, return everything
        if page is None:
            return values

        paginator = self.get_paginator(values, per_page=per_page)
        page = paginator.page(page)

        kwargs = {'pk': pk}
        if item_pk:
            kwargs['item_pk'] = item_pk
        path = reverse('vocab:items', kwargs=kwargs)
        links = self.get_page_links(request, path, page, extra=params)

        return {
            'values': page.object_list,
            'per_page': paginator.per_page,
            'num_pages': paginator.num_pages,
            'page_num': page.number,
            '_links': links,
        }


class ItemResource(ItemBaseResource):
    def get(self, request, pk, item_pk):
        return self.prepare(request, request.item, pk)
