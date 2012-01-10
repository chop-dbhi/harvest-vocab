from django.db import models, transaction

class ItemManager(models.Manager):
    def ancestors(self, pk, *args, **kwargs):
        "Returns a ``QuerySet`` containing all ancestors of this item."
        return self.get_query_set().get(pk=pk).ancestors(*args, **kwargs)

    def descendants(self, pk, *args, **kwargs):
        "Returns a ``QuerySet`` containing all descendants of this item."
        return self.get_query_set().get(pk=pk).descendants(*args, **kwargs)


class ItemIndexManager(models.Manager):
    def _index_ancestors(self, item, parent, depth=0):
        self.get_or_create(item=item, parent=parent, depth=depth)

        # recurse relative to next ancestor if exists
        if parent and parent.parent:
            self._index_ancestors(item, parent.parent, depth+1)

    @transaction.commit_on_success
    def index(self):
        indexed_model = self.model._meta.get_field_by_name('item')[0].rel.to

        items = indexed_model._default_manager.db_manager(self.db).all()

        for item in iter(items):
            self._index_ancestors(item, item.parent)

        # reset terminal flag
        items.update(terminal=False)

        indexes = self.get_query_set()

        # terminals are defined as having no children, thus the index will not
        # contain rows having ``item`` also be a ``parent``
        parents = indexes.exclude(parent=None).values_list('parent', flat=True)
        terminals = indexes.exclude(item__in=parents).distinct()\
            .values_list('item', flat=True)

        # update items that are terminals
        items.filter(pk__in=terminals).update(terminal=True)
