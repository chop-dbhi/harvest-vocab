from django.conf import settings
from django.core.urlresolvers import reverse
from avocado.criteria.viewset import AbstractViewSet

class VocabBrowserViewSet(AbstractViewSet):
    """Simple viewset for rendering a vocabulary _browser_.

    ``url_reversed`` must be defined either as a standalone string
    or a tuple of _reverse_-able arguments (name, args, kwargs).

    If ``search_only`` is True, no hierarchy browser will be displayed.
    """
    url_reversed = ''
    search_only = False

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
                'search_only': self.search_only,
                'js'  : STATIC_URL + 'vocab/js/vocabulary.js',
                'css' : STATIC_URL + 'vocab/css/vocabulary.css',
            }],
        }
