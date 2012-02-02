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

        from avocado.models import Field
        pk_field = Field.objects.get_by_natural_key(through._meta.app_label,
            through._meta.module_name, through.objects.object_field.name)

        condition = Q()
        if operator.uid == 'all':
            objects = field.model.objects.filter(pk__in=value)
            ids = through.objects.requires_all(objects)
            condition = self._condition(pk_field, inlist, ids, using)
        elif operator.uid == '-all':
            objects = field.model.objects.filter(pk__in=value)
            ids = through.objects.not_all(objects)
            condition = self._condition(pk_field, inlist, ids, using)
        elif operator.uid == 'only':
            objects = field.model.objects.filter(pk__in=value)
            ids = through.objects.only(objects)
            condition = self._condition(pk_field, inlist, ids, using)
        else:
            for pk in value:
                descendants = field.model.objects.descendants(pk, include_self=True)
                condition = condition | self._condition(field, operator, descendants, using)

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
