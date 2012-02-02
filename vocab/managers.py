from django.db import models, transaction, connection
from django.db.models.sql import RawQuery

quote_name = connection.ops.quote_name

class ItemManager(models.Manager):
    def ancestors(self, pk, *args, **kwargs):
        "Returns a ``QuerySet`` containing all ancestors of this item."
        return self.get_query_set().get(pk=pk).ancestors(*args, **kwargs)

    def descendants(self, pk, *args, **kwargs):
        "Returns a ``QuerySet`` containing all descendants of this item."
        return self.get_query_set().get(pk=pk).descendants(*args, **kwargs)


class ItemIndexThroughManager(models.Manager):
    def __init__(self, term_field_name, object_field_name):
        self._term_field_name = term_field_name
        self._object_field_name = object_field_name
        super(ItemIndexThroughManager, self).__init__()

    @property
    def term_field(self):
        return self.model._meta.get_field_by_name(self._term_field_name)[0]

    @property
    def object_field(self):
        return self.model._meta.get_field_by_name(self._object_field_name)[0]

    def _construct_case_statements(self, subqueries, true_value, false_value):
        "Constructs the case statements for the SQL string"
        query = []
        statement = 'SUM(CASE WHEN %(term_column)s = %(term_pk)s THEN %(true_value)s ' \
            'ELSE %(false_value)s END) AS %(column_alias)s'

        for descendants in subqueries:
            for term in descendants:
                query.append(statement % {
                    'term_column': quote_name(self.term_field.column),
                    'term_pk': term.pk,
                    'true_value': true_value,
                    'false_value': false_value,
                    'column_alias': quote_name('cname_' + str(term.pk)),
                })
        return ', '.join(query)

    def _construct_where_condition(self, subqueries, where_equals, child_join, node_join):
        """Constructs the conditions portion of the SQL string by setting each
        values row equal to where_equals. It joins each child condition by
        child_join and each top level condition by node_join.
        """
        query = []
        statement = ' %(column_alias)s = %(where_value)s '

        for descendants in subqueries:
            child_where = [statement % {
                'column_alias': quote_name('cname_' + str(term.pk)),
                'where_value': where_equals,
            } for term in descendants]
            query.append(' (' + child_join.join(child_where) + ') ')
        return node_join.join(query)

    def _get_query(self, subqueries, case_statements, where_conditions):
        """Constructs an SQL query based on the values, case_statments,
        and where conditions provided and runs the query on the associated
        model.
        """
        query = (
            'SELECT * FROM (SELECT %(object_column)s AS id, %(case_statements)s '
            'FROM %(through_table)s GROUP BY %(object_column)s) AS T WHERE %(where_condition)s' % {
                'object_column': quote_name(self.object_field.column),
                'case_statements': case_statements,
                'through_table': quote_name(self.model._meta.db_table),
                'where_condition': where_conditions,
            })

        return RawQuery(query, using=self.db)

    def requires_all(self, terms):
        "Returns through objects that are associated with 'all' of the given terms."
        subqueries = [term.descendants(include_self=True) for term in terms]
        case_statements = self._construct_case_statements(subqueries, 1, 0)
        where_condition = self._construct_where_condition(subqueries, 1, 'OR', 'AND')
        query = self._get_query(subqueries, case_statements, where_condition)

        # Raw queries are lightly wrapped cursors and are not pickleable so we must
        # evaluate it here
        ids = list(x[0] for x in query)
        return ids

    def not_all(self, terms):
        "Returns through objects that are _not_ associated with all of the given terms."
        subqueries = [term.descendants(include_self=True) for term in terms]
        case_statements = self._construct_case_statements(subqueries, 1, 0)
        where_condition = self._construct_where_condition(subqueries, 0, 'AND', 'OR')
        query = self._get_query(terms, case_statements, where_condition)

        # Raw queries are lightly wrapped cursors and are not pickleable so we must
        # evaluate it here
        ids = list(x[0] for x in query)
        return ids

    def only(self, terms):
        "Returns through objects that 'only' match the given terms."
        # TODO finding the descendants for an 'only' query does not make sense
        # since if an object is associated with a term (e.g. dog), the object won't
        # also be associated with a descendent term (e.g. beagle) that is more
        # specific. The more specific one implies the ancestory terms

        # Queries the index for the descendants of each term. These are the
        # complete sets that are applicable to this query
        subqueries = [term.descendants(include_self=True) for term in terms]

        # The values that the case statement will be set to if it has
        # the specified element
        set_value = -1 * (len(terms) - 1)

        case_statements = self._construct_case_statements(subqueries, set_value, 1)
        where_condition = self._construct_where_condition(subqueries, 0, 'OR', 'AND')
        query = self._get_query(subqueries, case_statements, where_condition)

        # Raw queries are lightly wrapped cursors and are not pickleable so we must
        # evaluate it here
        ids = list(x[0] for x in query)
        return ids


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
