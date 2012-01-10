from django.db import models, router
from django.db.models import Q
from vocab.managers import ItemManager, ItemIndexManager

class AbstractItem(models.Model):
    """The foreign key or many-to-many field to parent items must be defined.

    ``description_field`` should be set to the name or description char/text
    of the model. This is used for ordering and textual representation of
    ID-based queries (via the translator).

    ``search_fields`` are a list of fields that may be used for case-insensitive
    lookups (icontains). This is required for using Resource classes.
    """
    description_field = 'description'
    search_fields = ('description',)

    terminal = models.NullBooleanField()

    objects = ItemManager()

    class Meta(object):
        abstract = True

    def ancestors(self, include_self=False):
        "Returns a ``QuerySet`` containing all ancestors of this item."
        db = router.db_for_read(self.__class__, instance=self)
        subquery = self.item_indexes.db_manager(db).exclude(parent=None).values_list('parent__pk', flat=True)
        if include_self:
            return self.__class__.objects.db_manager(db).filter(Q(pk__in=subquery) | Q(pk=self.pk))
        return self.__class__.objects.db_manager(db).filter(pk__in=subquery)

    def descendants(self, include_self=False):
        "Returns a ``QuerySet`` containing all descendants of this item."
        db = router.db_for_read(self.__class__, instance=self)
        subquery = self.parent_indexes.db_manager(db).values_list('item__pk', flat=True)
        if include_self:
            return self.__class__.objects.db_manager(db).filter(Q(pk__in=subquery) | Q(pk=self.pk))
        return self.__class__.objects.db_manager(db).filter(pk__in=subquery)


class AbstractItemIndex(models.Model):
    "Foreign keys to the item and it's must parent must be defined."
    depth = models.IntegerField(default=0)

    objects = ItemIndexManager()

    def __unicode__(self):
        return u'%s via %s' % (self.item, self.parent)

    class Meta(object):
        abstract = True
        ordering = ('depth',)
