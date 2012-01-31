from django.db.models import Q
from django.core.exceptions import ImproperlyConfigured
from avocado.fields.translate import AbstractTranslator
from avocado.fields.operators import inlist, notinlist
from .operators import requireall, notall, only

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

        value = field.model.objects.filter(pk__in=value)

        # Start with an empty condition
        condition = Q()

        if operator.operator == 'all':
            ids = through.objects.requires_all(value)
            if ids:
                condition = self._condition(field, inlist, ids, using)
        elif operator.operator == '-all':
            ids = through.objects.not_all(value)
            if ids:
                condition = self._condition(field, inlist, ids, using)
        elif operator.operator == 'only':
            ids = through.objects.only(value)
            if ids:
                condition = self._condition(field, inlist, ids, using)
        else:
            for item in value:
                descendents = field.model.objects.descendents(item.pk, include_self=True)
                condition = condition | self._condition(field, operator, descendents, using)

        new_value = field.model.objects.filter(pk__in=value)\
            .values_list(field.model.description_field, flat=True)

        return {
            'condition': condition,
            'annotations': {},
            'cleaned_data': {
                'operator': operator,
                'value': value,
            },
            'raw_data': {
                'operator': roperator,
                'value': new_value,
            }
        }
