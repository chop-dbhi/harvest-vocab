"""
Example usage::

    class Procedure(AbstractItem):
        code = models.CharField(max_length=10)
        parent = models.ForeignKey('self', related_name='children')


    class ProcedureIndex(AbstractItemIndex):
        item = models.ForeignKey(Procedure, related_name='item_index')
        parent = models.ForeignKey(Procedure, related_name='parent_index')


"""

from django.db import models
from vocab.managers import ItemIndexManager

class AbstractItem(models.Model):
    "The foreign key or many-to-many field to parent items must be defined."

    search_fields = ('name',)

    terminal = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        abstract = True

    def ancestors(self, include_self=False):
        "Returns a ``QuerySet`` containing all ancestors of this item."
        ids = self.item_indexes.exclude(parent=None).values_list('parent', flat=True)
        if include_self:
            ids += [self.pk]
        return self.__class__.objects.filter(pk__in=ids)

    def descendents(self, include_self=False):
        "Returns a ``QuerySet`` containing all descendents of this item."
        ids = self.parent_indexes.values_list('item', flat=True)
        if include_self:
            ids = [self.pk] + ids
        return self.__class__.objects.filter(pk__in=ids)


class AbstractItemIndex(models.Model):
    "Foreign keys to the item and it's must parent must be defined."
    depth = models.IntegerField(default=0)

    objects = ItemIndexManager()

    def __unicode__(self):
        return u'%s via %s' % (self.item, self.parent)

    class Meta(object):
        abstract = True
        ordering = ('depth',)
