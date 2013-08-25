import re
from django.db import models, transaction, connection
from django.db.models.sql import RawQuery

qn = connection.ops.quote_name

# Prefix for the summed case statement values
COLUMN_PREFIX = 'sc'

# Case statement for determining if the lookup matches the item or the
# parent. Every record is evaluated
SUMMED_CASE_TEMPLATE = '''\
SUM(
    CASE
        WHEN {index_table}.{item_column} = {item_pk} THEN 1
        WHEN {index_table}.{parent_column} = {item_pk} THEN 1
        ELSE 0
    END
) AS {column_alias}
'''

# Sub-query which selects all object ids matching the conditions derived
# from the CASE statements.
PIVOT_QUERY_TEMPLATE = '''\
SELECT {object_column} FROM (
    SELECT {object_column}, {case_statements}
    FROM {through_table}
        INNER JOIN {index_table} ON ({through_table}.{item_column} = {index_table}.{item_id})
    GROUP BY {object_column}
) AS T WHERE {negate} ({where_condition})
'''


class ItemManager(models.Manager):
    def ancestors(self, pk, *args, **kwargs):
        "Returns a ``QuerySet`` containing all ancestors of this item."
        return self.get_query_set().get(pk=pk).ancestors(*args, **kwargs)

    def descendants(self, pk, *args, **kwargs):
        "Returns a ``QuerySet`` containing all descendants of this item."
        return self.get_query_set().get(pk=pk).descendants(*args, **kwargs)


class ItemThroughManager(models.Manager):
    def __init__(self, item_field_name, object_field_name):
        self._item_field_name = item_field_name
        self._object_field_name = object_field_name
        super(ItemThroughManager, self).__init__()

    @property
    def item_field(self):
        "Reference to the local foreign key reference to the `AbstractItem` subclass."
        return self.model._meta.get_field_by_name(self._item_field_name)[0]

    @property
    def object_field(self):
        "Reference to the local foreign key reference to the related object."
        return self.model._meta.get_field_by_name(self._object_field_name)[0]

    @property
    def index_model(self):
        "Reference to the item's `AbstractItemIndex` subclass."
        return self.item_field.rel.to.item_indexes.related.model

    def _construct_case_and_where(self, items, where_equals, node_join):
        """Constructs the SUM-CASE statement and corresponding WHERE clause
        for each item. WHERE clauses are set to `where_equals` and joined by
        the `node_join` operator, either AND or OR.
        """
        cases = []
        wheres = []

        if where_equals is True:
            predicate = ' {column_alias} > 0 '
        else:
            predicate = ' {column_alias} = {where_equals} '

        for pk in items:
            column_alias = COLUMN_PREFIX + str(pk)

            cases.append(SUMMED_CASE_TEMPLATE.format(**{
                'item_pk': pk,
                'index_table': qn(self.index_model._meta.db_table),
                'item_column': qn('item_id'),
                'parent_column': qn('parent_id'),
                'column_alias': qn(column_alias),
            }))

            wheres.append(predicate.format(column_alias=qn(column_alias),
                where_equals=where_equals))

        return ', '.join(cases), node_join.join(wheres)

    def _get_query(self, case_statements, where_conditions, evaluate, negate=False):
        """Constructs an SQL query based on the items, case_statments,
        and where conditions provided and runs the query on the associated
        model.
        """
        query = PIVOT_QUERY_TEMPLATE.format(**{
            'item_column': qn(self.item_field.column),
            'object_column': qn(self.object_field.column),
            'case_statements': case_statements,
            'through_table': qn(self.model._meta.db_table),
            'index_table': qn(self.index_model._meta.db_table),
            'where_condition': where_conditions,
            'item_id': qn('item_id'),
            'negate': negate and 'NOT' or '',
        })
        # Clean up the whitespace
        query = re.sub('\s+', ' ', query)
        if evaluate:
            return [x[0] for x in RawQuery(query, using=self.db)]
        return '({0})'.format(query)

    def _prepare_items(self, items):
        if type(items[0]) is not int:
            items = [term.pk for term in items]
        return items

    def _any(self, items, evaluate, negate):
        "Pivot query for disjunction."
        items = self._prepare_items(items)
        cases, wheres = self._construct_case_and_where(items, True, 'OR')
        return self._get_query(cases, wheres, evaluate, negate)

    def _all(self, items, evaluate, negate):
        "Pivot query for conjunction."
        items = self._prepare_items(items)
        cases, wheres = self._construct_case_and_where(items, True, 'AND')
        return self._get_query(cases, wheres, evaluate, negate)

    def _only(self, items, evaluate, negate):
        "Pivot query for exclusive conjunction."
        items = self._prepare_items(items)
        cases, wheres = self._construct_case_and_where(items, 1, 'AND')
        return self._get_query(cases, wheres, evaluate)

    def requires_any(self, items, evaluate=False):
        return self._any(items, evaluate, negate=False)

    def excludes_any(self, items, evaluate=False):
        return self._any(items, evaluate, negate=True)

    def requires_all(self, items, evaluate=False):
        return self._all(items, evaluate, negate=False)

    def excludes_all(self, items, evaluate=False):
        return self._all(items, evaluate, negate=True)

    def only(self, items, evaluate=False):
        return self._only(items, evaluate, negate=False)


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
