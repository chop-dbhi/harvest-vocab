from django.db import models
from django.test import TestCase
from vocab.models import AbstractItem, AbstractItemIndex

class Ticket(AbstractItem):
    search_fields = ('name', 'description')

    name = models.CharField(max_length=50)
    description = models.TextField(null=True)
    parent = models.ForeignKey('self', null=True, related_name='children')


class TicketIndex(AbstractItemIndex):
    item = models.ForeignKey(Ticket, related_name='item_indexes')
    parent = models.ForeignKey(Ticket, null=True, related_name='parent_indexes')


class ItemTestCase(TestCase):
    def setUp(self):
        TicketIndex.objects.index()

    def test_ancestors(self):
        tickets = {
            1: [],
            2: [1],
            3: [],
            4: [3],
            5: [3, 4],
            6: [3],
            7: [3, 4, 5],
        }

        for ticket in Ticket.objects.iterator():
            ancestors = ticket.ancestors().values_list('pk', flat=True)
            self.assertEqual(list(ancestors), tickets[ticket.id])

    def test_descendents(self):
        tickets = {
            1: [2],
            2: [],
            3: [4, 5, 6, 7],
            4: [5, 7],
            5: [7],
            6: [],
            7: [],
        }

        for ticket in Ticket.objects.iterator():
            descendents = ticket.descendents().values_list('pk', flat=True)
            self.assertEqual(list(descendents), tickets[ticket.id])

    def test_terminals(self):
        terminals = Ticket.objects.filter(terminal=True).values_list('pk', flat=True)
        self.assertEqual(list(terminals), [2, 6, 7])

