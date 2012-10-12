from django.db import connection
from django.core.exceptions import ImproperlyConfigured
from avocado.query.translators import Translator, registry
from modeltree.tree import trees

qn = connection.ops.quote_name

class VocabularyTranslator(Translator):
    through_model = None
   
    operators = ('in', '-in', '-all', 'all', 'only')

    def __init__(self, *args, **kwargs):
        if not self.through_model:
            raise ImproperlyConfigured('Translator requires `through_model` attribute be defined')
        super(VocabularyTranslator, self).__init__(*args, **kwargs)

    def translate(self, field, roperator, rvalue, using, **context):
        operator, value = self.validate(field, roperator, rvalue, using, **context)
        condition = self._condition(field, operator, value, using)
        language = self.language(field, roperator, rvalue, using, **context)
    
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
        joins = tree.get_joins(through.objects.object_field.rel.to)
        # Skip the first join connection since it
        tables = []
        where = []
        v=[]
        if len(joins) > 1:
            for join in joins[1:]:
                conn = join.get('connection')
                if len(conn) != 4:
                    return conn
                v.append(conn)
                
                #for left, right, left_id, right_id in conn:
                left = conn[0]
                right = conn[1]
                left_id = conn[2]
                right_id=conn[3]

                tables.append(right)
                where.append('%s.%s = %s.%s' % (qn(left), qn(left_id), qn(right), qn(right_id)))

        where.append('%(object_table)s.%(object_id)s %(operator)s %(subquery)s' % {
            'operator': 'NOT IN' if operator.negated else 'IN',
            'object_table': qn(through.objects.object_field.rel.to._meta.db_table),
            'object_id': qn(through.objects.object_field.rel.to._meta.pk.column),
            'subquery': subquery,
        })
      
        new_value = [v.description for v in value]
            
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
                    'where':where,
                    'tables':tables,

                },
            }
        }
