from django.db import connection
from django.core.exceptions import ImproperlyConfigured
from avocado.fields.translate import AbstractTranslator
from avocado.fields.operators import inlist, notinlist
from avocado.modeltree import trees
from .operators import requireall, notall, only

qn = connection.ops.quote_name

class VocabularyTranslator(AbstractTranslator):
    through_model = None
    operators = (inlist, notinlist, requireall, notall, only)

    def __init__(self, *args, **kwargs):
        if not self.through_model:
            raise ImproperlyConfigured('Translator requires `through_model` attribute be defined')
        super(VocabularyTranslator, self).__init__(*args, **kwargs)

    def translate(self, field, roperator, rvalue, using, **context):
        operator, value = self.validate(field, roperator, rvalue, **context)

        through = self.through_model

        if operator.uid == 'in':
            subquery = through.objects.requires_any(value)
        elif operator.uid == '-in':
            subquery = through.objects.excludes_any(value)
        elif operator.uid == 'all':
            subquery = through.objects.requires_all(value)
        elif operator.uid == '-all':
            subquery = through.objects.excludes_all(value)
        elif operator.uid == 'only':
            subquery = through.objects.only(value)
        else:
            raise ImproperlyConfigured()

        tree = trees[using]
        joins = tree.get_all_join_connections(tree.path_to(through.objects.object_field.rel.to))
        # Skip the first join connection since it
        tables = []
        where = []

        if len(joins) > 1:
            for left, right, left_id, right_id in joins[1:]:
                tables.append(right)
                where.append('%s.%s = %s.%s' % (qn(left), qn(left_id), qn(right), qn(right_id)))

        where.append('%(object_table)s.%(object_id)s %(operator)s %(subquery)s' % {
            'operator': 'NOT IN' if operator.negated else 'IN',
            'object_table': qn(through.objects.object_field.rel.to._meta.db_table),
            'object_id': qn(through.objects.object_field.rel.to._meta.pk.column),
            'subquery': subquery,
        })

        new_value = field.model.objects.filter(pk__in=value)\
            .values_list(field.model.description_field, flat=True)

        return {
            'extra': {'where': where, 'tables': tables},
            'cleaned_data': {
                'operator': operator,
                'value': value,
            },
            'raw_data': {
                'operator': roperator,
                'value': new_value,
            }
        }
