from django.db import models
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

