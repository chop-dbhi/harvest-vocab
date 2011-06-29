from django.conf import settings
from django.core.urlresolvers import reverse
from avocado.criteria.viewset import AbstractViewSet

class VocabBrowserViewSet(AbstractViewSet):

    def browser(self, concept, cfields, *args, **kwargs):
        STATIC_URL =  settings.STATIC_URL

        if type(self.url_reversed) is str:
            url = reverse(self.url_reversed)
        else:
            url = reverse(*self.url_reversed)

        concept_id = str(concept.id)

        return {
            'join_by': "or",
            'elements':[{
                'pk' : cfields[0].field.pk,
                'title': concept.name,
                'type':'custom',
                'directory': url,
                'js'  : STATIC_URL + 'vocab/js/vocabulary.js',
                'css' : STATIC_URL + 'vocab/css/vocabulary.css',
            }],

        }
