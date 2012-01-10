from avocado.fields.translate import AbstractTranslator

class VocabularyTranslator(AbstractTranslator):
    """Cross queries the """
    def translate(self, field, roperator, rvalue, using, **context):
        meta = super(VocabularyTranslator, self).translate(field, roperator,
            rvalue, using, **context)

        cleaned_data = meta['cleaned_data']
        description_field = field.model.description_field

        # get all descedents for all top-level items that were selected        
        subquery = field.model.objects.none()
        for pk in cleaned_data['value']:
            subquery = subquery | field.model.objects.descendants(pk, include_self=True)

        meta['condition'] = self._condition(field, cleaned_data['operator'], subquery, using)

        # get the textual representations of the items being queried.
        # `raw_data` is used strictly for keeping track of the request data.
        # we replace the 'value' with these more readable values for downstream
        # interpretation
        values = cleaned_data['value']
        new_value = field.model.objects.filter(pk__in=values)\
            .values_list(description_field, flat=True)
        meta['raw_data']['value'] = new_value

        return meta
