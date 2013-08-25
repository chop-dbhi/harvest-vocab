from django.db.models import Q
from django.db import models, router
from vocab.managers import ItemManager, ItemIndexManager

class AbstractItem(models.Model):
    """Abstract class for a hierarchical item to be used with the vocab
    facilities.

    The foreign key or many-to-many `parent` field must be defined in concrete
    subclasses.

    The supplied `terminal` field is for operational purposes but can used as
    a shorthand way for finding all terminals/leaves in the tree. This value
    is set by the `ItemIndexManager` after an index is rebuilt.

    `description_field` is the name or description char/text field
    representative the item. This is used for ordering and textual
    representation of ID-based queries.

    `search_fields` are a list of fields that may be used for
    case-insensitive lookups (icontains). This is required for using the API
    resource classes.
    """
    terminal = models.NullBooleanField()

    objects = ItemManager()
    description_field = 'description'
    search_fields = ('description',)

    class Meta(object):
        abstract = True

    def __unicode__(self):
        return unicode(getattr(self, self.description_field))

    def ancestors(self, include_self=False):
        """Returns a `QuerySet` containing all ancestors of this item.

        If `include_self` is true, this item will be included in the query
        set.
        """
        db = router.db_for_read(self.__class__, instance=self)
        subquery = self.item_indexes.db_manager(db).exclude(parent=None).values_list('parent__pk', flat=True)
        if include_self:
            return self.__class__.objects.db_manager(db).filter(Q(pk__in=subquery) | Q(pk=self.pk))
        return self.__class__.objects.db_manager(db).filter(pk__in=subquery)

    def descendants(self, include_self=False):
        """Returns a `QuerySet` containing all descendants of this item.

        If `include_self` is true, this item will be included in the query
        set.
        """
        db = router.db_for_read(self.__class__, instance=self)
        subquery = self.parent_indexes.db_manager(db).values_list('item__pk', flat=True)
        if include_self:
            return self.__class__.objects.db_manager(db).filter(Q(pk__in=subquery) | Q(pk=self.pk))
        return self.__class__.objects.db_manager(db).filter(pk__in=subquery)


class AbstractItemIndex(models.Model):
    """Abstract class for an item index.

    Foreign keys named `item` and `parent` must be defined referencing an
    `AbstractItem` subclass.
    """
    depth = models.IntegerField(default=0)

    objects = ItemIndexManager()

    def __unicode__(self):
        return u'{0} via {1}'.format(self.item, self.parent)

    class Meta(object):
        abstract = True
        ordering = ('depth',)
