from django.db import models
from django.test import TestCase
from vocab.models import AbstractItem, AbstractItemIndex
from vocab.managers import ItemIndexThroughManager

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

    objects = ItemIndexThroughManager('ticket', 'holder')


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

    def test_requires_all(self):
        values = [Ticket.objects.db_manager('alt').get(pk=3), Ticket.objects.db_manager('alt').get(pk=1)]

        id_nums = TicketThrough.objects.db_manager('alt').requires_all(values)

        self.assertEqual(list(id_nums), [1,3])
        holders = TicketHolder.objects.filter(id__in=id_nums).values_list('name', flat=True)

        self.assertEqual(list(holders), ['Ada Lovelace', 'Grace Hopper'])

    def test_not_all(self):
        values = [Ticket.objects.db_manager('alt').get(pk=1), Ticket.objects.db_manager('alt').get(pk=5)]

        id_nums = TicketThrough.objects.db_manager('alt').not_all(values)

        self.assertEqual(list(id_nums), [1,2])
        holders = TicketHolder.objects.filter(id__in=id_nums).values_list('name', flat=True)

        self.assertEqual(list(holders), ['Ada Lovelace', 'Charles Babbage'])

    def test_only(self):
        values = [Ticket.objects.db_manager('alt').get(pk=1), Ticket.objects.db_manager('alt').get(pk=5), Ticket.objects.db_manager('alt').get(pk=6)]

        id_nums = TicketThrough.objects.db_manager('alt').only(values)

        self.assertEqual(list(id_nums), [3])
        holders = TicketHolder.objects.filter(id__in=id_nums).values_list('name', flat=True)

        self.assertEqual(list(holders), ['Grace Hopper'])
