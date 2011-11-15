from django.db import models, transaction, connection
from django.utils.datastructures import SortedDict
import string

class ItemManager(models.Manager):
    def ancestors(self, pk, *args, **kwargs):
        "Returns a ``QuerySet`` containing all ancestors of this item."
        return self.get_query_set().get(pk=pk).ancestors(*args, **kwargs)

    def descendants(self, pk, *args, **kwargs):
        "Returns a ``QuerySet`` containing all descendants of this item."
        return self.get_query_set().get(pk=pk).descendants(*args, **kwargs)

class ItemIndexThroughManager(models.Manager):

    def _construct_case_statements(self, values, true_value, false_value):
        ''' Constructs the case statements for the SQL string
        '''
        qn = connection.ops.quote_name
        query = []
        for val in values:
            for v in val:
                query.append("SUM(CASE WHEN %(source_column)s = %(value)s"
                    " THEN %(true_value)s ELSE %(false_value)s END) AS"
                    " %(column_alias)s" %
                    {'source_column': qn(v._meta.module_name + "_id"),
                    'value': v.id,
                    'true_value' : true_value,
                    'false_value' : false_value,
                    'column_alias' : qn("cname_" + str(v.id)),})
        return ", ".join(query)


    def _construct_where_condition(self, values, where_equals, child_join,
                                node_join):
        ''' Constructs the conditions portion of the SQL string by setting each
        values row equal to where_equals. It joins each child condition by
        child_join and each top level condition by node_join
        '''
        qn = connection.ops.quote_name
        query = []
        for val in values:
            child_where = [" %(column_alias)s = %(where_value)s " %
                {'column_alias': qn("cname_"+str(v.id)),
                'where_value' : where_equals} for v in val]
            child_where = child_join.join(child_where)
            query.append(" (" + child_where + ") ")
        return node_join.join(query)

    def _get_query(self, values, case_statements, where_conditions):
        ''' Constructs an SQL query based on the values, case_statments,
        and where conditions provided and runs the query on the associated
        model.
        '''
        qn = connection.ops.quote_name

        name = values[0][0]._meta.module_name
        fields = self.model._meta.fields

        for f in fields:
            if isinstance(f, models.ForeignKey):
                if f.name != name:
                    target_column = f.name + '_id'
        
        query = "SELECT * FROM (" \
            " SELECT %(target_column)s AS id, %(case_statements)s FROM" \
            " %(through_table)s GROUP BY %(target_column)s) AS T WHERE " \
            " %(where_condition)s" \
            %{'target_column' : qn(target_column) ,
                'case_statements' : case_statements,
                'through_table' : qn(self.model._meta.db_table),
                'where_condition' : where_conditions}

        return query

    def requires_all(self, values):
        ''' If all of the values match for an element, it is returned in the
        query.
        '''
        if isinstance(values,list) and len(values) > 0:
            values = [v.descendents(include_self=True) for v in values]
            case_statements = self._construct_case_statements(values, 1, 0)
            where_condition = self._construct_where_condition(values, 1, "OR",
                                    "AND")
            query = self._get_query(values, case_statements, where_condition)
            return self.model.objects.raw(query)
        else:
            raise ValueError("requires_all: %(values)s is not a list with" \
                " greater than 0 elements." %{'values' : values})

    def not_all(self, values):
        ''' If any of the values match for an element, it is NOT returned in
        the query.
        '''
        if isinstance(values,list) and len(values) > 0:
            values = [v.descendents(include_self=True) for v in values]
            case_statements = self._construct_case_statements(values, 1, 0)
            where_condition = self._construct_where_condition(values, 0, "AND",
                                        "OR")
            query = self._get_query(values, case_statements, where_condition)
            return self.model.objects.raw(query)
        else:
            raise ValueError("not_all: %(values)s is not a list with" \
                "greater than 0 elements." %{'values' : values})
    
    def only(self, values):
        ''' If any of the values match for an element, it is NOT returned in
        the query.
        '''
        if isinstance(values,list) and len(values) > 0:
            values = [v.descendents(include_self=True) for v in values]

            ''' The values that the case statement will be set to if it has
            the specified element'''
            set_value = -1 * (len(values) - 1)

            case_statements = self._construct_case_statements(values,
                                    set_value, 1)
            where_condition = self._construct_where_condition(values, 0, "OR",
                                    "AND")
            query = self._get_query(values, case_statements, where_condition)
            return self.model.objects.raw(query)
        else:
            raise ValueError("only: %(values)s is not a list with greater" \
                " than 0 elements." %{'values' : values})

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
