from django.test import TestCase
from django.core import management
from avocado.models import DataField
from vocab.translators import VocabularyTranslate

class TranslatorTestCase(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        management.call_command('avocado','init')
        self.t = VocabularyTranslate()
        print self.t

    def test_this(self):
        print self.t
        print "hello"
