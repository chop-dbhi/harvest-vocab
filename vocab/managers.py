from django.db import models, transaction

class ItemManager(models.Manager):
    def ancestors(self, pk, *args, **kwargs):
        "Returns a ``QuerySet`` containing all ancestors of this item."
        return self.get_query_set().get(pk=pk).ancestors(*args, **kwargs)

    def descendants(self, pk, *args, **kwargs):
        "Returns a ``QuerySet`` containing all descendants of this item."
        return self.get_query_set().get(pk=pk).descendants(*args, **kwargs)

class ItemIndexThroughManager(models.Manager):

    def _get_select(self, values, then_val, else_val):
        ''' Returns the select portion of the query based on the values
        '''
        name = values[0][0]._meta.module_name
        fields = self.model._meta.fields
        through_name = self.model._meta.db_table

        for f in fields:
            if isinstance(f, models.ForeignKey):
                if f.name != name:
                     id_name = f.name+'_id'

        name_id = name + "_id"
        query = "SELECT * FROM (SELECT " + id_name + " as id, "

        for val in values:
            for v in val:
                query += "SUM(CASE WHEN %s = %s THEN %s ELSE %s END) as \"%s\", " %(name_id, v.id, then_val, else_val, "cname_" + str(v.id))
        query = query[:len(query)-2] + " FROM %s GROUP BY %s) AS T" %(through_name, id_name)

        return query

    def requires_all(self, values):
        ''' If all of the values match for an element, it is returned in the
        query.
        '''
        values = [v.descendents(include_self=True) for v in values]
        q = self._get_select(values, 1, 0) + " WHERE "
        for val in values:
            q += " ("
            for v in val:
                q += ("\"%s\" = 1 OR " %("cname_"+str(v.id)))
            q = q[:len(q)-3] + ")AND "
        q = q[:len(q)-4]+";"

        return self.model.objects.raw('%s' %q)

    def not_all(self, values):
        ''' If any of the values match for an element, it is NOT returned in
        the query.
        '''
        values = [v.descendents(include_self=True) for v in values]
        q = self._get_select(values, 1, 0) + " WHERE "
        for val in values:
            q += " ("
            for v in val:
                q += "\"%s\" = 0 AND " %("cname_"+str(v.id))
            q = q[:len(q)-4] + ")OR "
        q = q[:len(q)-3]+";"

        return self.model.objects.raw('%s' %q)

    def only(self, values):
        ''' If any of the values match for an element, it is NOT returned in
        the query.
        '''
        values = [v.descendents(include_self=True) for v in values]
        result = -1 * (len(values) - 1)
        q = self._get_select(values, result , 1)+ " WHERE "
        for val in values:
            q += " ("
            for v in val:
                q += "\"%s\" = %s OR " %("cname_"+str(v.id), 0)
            q = q[:len(q)-3] + ") AND "
        q = q[:len(q)-4]+";"
        return self.model.objects.raw('%s' %q)

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
