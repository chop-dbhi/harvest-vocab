import re
from django.db import models, transaction, connection
from django.db.models.sql import RawQuery

qn = connection.ops.quote_name

COLUMN_PREFIX = 'ct_'

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

    def _construct_case_statements(self, values, true_value, false_value):
        "Constructs the case statements for the SQL string"
        statement = '''
            SUM(
                CASE
                    WHEN %(index_table)s.%(item_column)s = %(item_pk)s THEN %(true_value)s
                    WHEN %(index_table)s.%(parent_column)s = %(item_pk)s THEN %(true_value)s
                    ELSE %(false_value)s
                END
            ) AS %(column_alias)s
        '''

        query = [statement % {
            'item_pk': pk,
            'index_table': qn(self.index_model._meta.db_table),
            'item_column': qn('item_id'),
            'parent_column': qn('parent_id'),
            'true_value': true_value,
            'false_value': false_value,
            'column_alias': qn(COLUMN_PREFIX + str(pk)),
        } for pk in values]
        return ', '.join(query)

    def _construct_where_condition(self, values, where_equals, node_join):
        """Constructs the conditions portion of the SQL string by setting each
        values row equal to `where_equals`.
        """
        if where_equals is True:
            statement = ' %(column_alias)s > 0 '
        else:
            statement = ' %(column_alias)s = %(where_equals)s '

        query = [statement % {
            'column_alias': qn(COLUMN_PREFIX + str(pk)),
            'where_equals': where_equals,
        } for pk in values]
        return node_join.join(query)

    def _get_query(self, case_statements, where_conditions, evaluate):
        """Constructs an SQL query based on the values, case_statments,
        and where conditions provided and runs the query on the associated
        model.
        """
        query = '''
            SELECT %(object_column)s FROM (
                SELECT %(object_column)s, %(case_statements)s
                FROM %(through_table)s
                    INNER JOIN %(index_table)s ON (%(through_table)s.%(item_column)s = %(index_table)s.%(item_id)s)
                GROUP BY %(object_column)s
            ) AS T WHERE %(where_condition)s
        ''' % {
            'item_column': qn(self.item_field.column),
            'object_column': qn(self.object_field.column),
            'case_statements': case_statements,
            'through_table': qn(self.model._meta.db_table),
            'index_table': qn(self.index_model._meta.db_table),
            'where_condition': where_conditions,
            'item_id': qn('item_id'),
        }
        # Clean up the whitespace
        query = re.sub('\s+', ' ', query)
        if evaluate:
            return [x[0] for x in RawQuery(query, using=self.db)]
        return '(%s)' % query

    def requires_any(self, items, evaluate=False):
        "Returns through objects that are associated with 'any' of the given items."
        if type(items[0]) is not int:
            items = [term.pk for term in items]
        case_statements = self._construct_case_statements(items, 1, 0)
        where_condition = self._construct_where_condition(items, True, 'OR')
        return self._get_query(case_statements, where_condition, evaluate)

    def requires_all(self, items, evaluate=False):
        "Returns through objects that are associated with 'all' of the given items."
        if type(items[0]) is not int:
            items = [term.pk for term in items]
        case_statements = self._construct_case_statements(items, 1, 0)
        where_condition = self._construct_where_condition(items, True, 'AND')
        return self._get_query(case_statements, where_condition, evaluate)

    def excludes_all(self, items, evaluate=False):
        "Returns through objects that are _not_ associated with all of the given items."
        if type(items[0]) is not int:
            items = [term.pk for term in items]
        case_statements = self._construct_case_statements(items, 1, 0)
        where_condition = self._construct_where_condition(items, True, 'AND')
        return self._get_query(case_statements, where_condition, evaluate)

    def excludes_any(self, items, evaluate=False):
        if type(items[0]) is not int:
            items = [term.pk for term in items]
        case_statements = self._construct_case_statements(items, 1, 0)
        where_condition = self._construct_where_condition(items, True, 'OR')
        return self._get_query(case_statements, where_condition, evaluate)

    def only(self, items, evaluate=False):
        "Returns through objects that 'only' match the given items."
        if type(items[0]) is not int:
            items = [term.pk for term in items]
        case_statements = self._construct_case_statements(items, 1, 0)
        where_condition = self._construct_where_condition(items, 1, 'AND')
        return self._get_query(case_statements, where_condition, evaluate)


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
