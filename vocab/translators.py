from django.db import connection
from django.core.exceptions import ImproperlyConfigured
from avocado.query.translators import Translator
from modeltree.tree import trees

qn = connection.ops.quote_name

class VocabularyTranslator(Translator):
    through_model = None

    operators = ('in', '-in', '-all', 'all', 'only')

    def __init__(self, *args, **kwargs):
        if not self.through_model:
            raise ImproperlyConfigured('Translator requires `through_model` attribute be defined')
        super(VocabularyTranslator, self).__init__(*args, **kwargs)

    def translate(self, field, roperator, rvalue, tree, **context):
        # Validate the operator and value
        operator, value = self.validate(field, roperator, rvalue, tree, **context)

        # Build the default language representation
        language = self.language(field, operator, value, tree=tree, **context)

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
            raise ImproperlyConfigured('Unknown operator for vocab translator')

        # Get all joins from the target tree model to the 'object' field on
        # the through model.
        tree = trees[tree]
        joins = tree.get_joins(through.objects.object_field.rel.to)

        # Collect where/tables information required for the `QuerySet.extra()`
        # method. See: https://docs.djangoproject.com/en/1.5/ref/models/querysets/#extra
        tables = []
        where = []

        for join in joins[1:]:
            conn = join.get('connection')

            tables.append(right)

            kwargs = {
                'left': qn(conn[0]),
                'right': qn(conn[1]),
                'left_id': qn(conn[2]),
                'right_id': qn(conn[3]),
            }

            where.append('{left}.{left_id} = {right}.{right_id}'.format(**kwargs))

        where.append('{object_table}.{object_id} IN {subquery}'.format(**{
            'object_table': qn(through.objects.object_field.rel.to._meta.db_table),
            'object_id': qn(through.objects.object_field.rel.to._meta.pk.column),
            'subquery': subquery,
        }))

        # Extract description of each 'value' which will be the item object
        # itself.
        new_value = [unicode(v) for v in value]

        return {
            'id': field.pk,
            'operator': roperator,
            'value' : new_value,
            'cleaned_data':{
                'value': value,
                'operator': operator,
                'language': language,
            },
            'query_modifiers': {
                'condition': None,
                'annotations': None,
                'extra': {
                    'where': where,
                    'tables': tables,
                },
            }
        }
