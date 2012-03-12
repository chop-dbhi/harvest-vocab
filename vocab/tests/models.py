from django.db import models
from django.test import TestCase
from vocab.models import AbstractItem, AbstractItemIndex
from vocab.managers import ItemThroughManager

class Ticket(AbstractItem):
    search_fields = ('name', 'description')

    name = models.CharField(max_length=50)
    description = models.TextField(null=True)
    parent = models.ForeignKey('self', null=True, related_name='children')


class TicketIndex(AbstractItemIndex):
    item = models.ForeignKey(Ticket, related_name='item_indexes')
    parent = models.ForeignKey(Ticket, null=True, related_name='parent_indexes')


class TicketHolder(models.Model):
    name = models.CharField(max_length=50)
    tickets = models.ManyToManyField(Ticket, through="TicketThrough")


class TicketThrough(models.Model):
    holder = models.ForeignKey(TicketHolder, related_name = 'holder_thr')
    ticket = models.ForeignKey(Ticket, null=True, related_name='ticket_thr')

    objects = ItemThroughManager('ticket', 'holder')


class ItemTestCase(TestCase):
    def setUp(self):
        TicketIndex.objects.db_manager('alt').index()

    def test_ancestors(self):
        tickets = {
            1: [1],
            2: [1, 2],
            3: [3],
            4: [3, 4],
            5: [3, 4, 5],
            6: [3, 6],
            7: [3, 4, 5, 7],
        }

        for ticket in Ticket.objects.using('alt').iterator():
            ancestors = ticket.ancestors(include_self=True).values_list('pk', flat=True)
            self.assertEqual(list(ancestors), tickets[ticket.id])

    def test_descendants(self):
        tickets = {
            1: [2],
            2: [],
            3: [4, 5, 6, 7],
            4: [5, 7],
            5: [7],
            6: [],
            7: [],
        }

        for ticket in Ticket.objects.using('alt').iterator():
            descendants = ticket.descendants().values_list('pk', flat=True)
            self.assertEqual(list(descendants), tickets[ticket.id])

    def test_terminals(self):
        terminals = Ticket.objects.using('alt').filter(terminal=True).values_list('pk', flat=True)
        self.assertEqual(list(terminals), [2, 6, 7])

    def test_requires_any(self):
        # Holder must be assigned at least one of the tickets..
        values = [3]
        ids = TicketThrough.objects.db_manager('alt').requires_any(values, evaluate=True)
        holders = TicketHolder.objects.filter(id__in=ids).values_list('pk', flat=True)
        self.assertEqual(list(holders), [1, 2, 3])

    def test_requires_all(self):
        # Holder must be assigned both tickets..
        values = [1, 3]
        ids = TicketThrough.objects.db_manager('alt').requires_all(values, evaluate=True)
        holders = TicketHolder.objects.filter(id__in=ids).values_list('pk', flat=True)
        self.assertEqual(list(holders), [1, 3])

    def test_excludes_all(self):
        # Holder must not be assigned to both tickets..
        values = [1, 5]
        ids = TicketThrough.objects.db_manager('alt').excludes_all(values, evaluate=True)
        holders = TicketHolder.objects.filter(id__in=ids).values_list('pk', flat=True)
        self.assertEqual(list(holders), [2])

    def test_excludes_any(self):
        # Holder must not be assigned to either tickets..
        values = [1, 2]
        ids = TicketThrough.objects.db_manager('alt').excludes_any(values, evaluate=True)
        holders = TicketHolder.objects.filter(id__in=ids).values_list('pk', flat=True)
        self.assertEqual(list(holders), [2, 3])

    def test_only(self):
        # Holder must be assigned to only these tickets..
        values = [1, 6]
        ids = TicketThrough.objects.db_manager('alt').only(values, evaluate=True)
        holders = TicketHolder.objects.filter(id__in=ids).values_list('pk', flat=True)
        self.assertEqual(list(holders), [3])
