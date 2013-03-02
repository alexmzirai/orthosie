from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

class Shift(models.Model):
    begin_date = models.DateTimeField(auto_now=True)
    finish_date = models.DateTimeField(null=True)

    def __unicode__(self):
        return str(self.begin_date) + ' to ' + str(self.finish_date)

    def end_shift(self):
        if self.finish_date == None:
            self.finish_date = timezone.now()

    def create_transaction(self):
        if self.finish_date == None:
            return self.transaction_set.create(begin_date=timezone.now())

class Transaction(models.Model):
    shift = models.ForeignKey(Shift)
    begin_date = models.DateTimeField()
    finish_date = models.DateTimeField(null=True)
    status = models.CharField(max_length=10, default='Started')

    def __unicode__(self):
        return str(self.begin_date) + ' to ' + str(self.finish_date)

    def end_transaction(self):
        if self.finish_date == None:
            self.finish_date = timezone.now()

    def create_line_item(self, item, quantity, scale=None):
        if self.finish_date == None:
            return self.lineitem_set.create(\
                item=item,\
                quantity=quantity,\
                upc=item.upc,\
                scale=scale,\
                description=item.vendor.name + ' ' + item.name,\
                price=item.price\
            )

    def get_totals(self):
        total = 0
        tax = 0
        for line_item in self.lineitem_set.all():
            total = total + line_item.price
            if line_item.item.taxable:
                tax = Decimal(tax) + line_item.price * Decimal('.07')
        tax = tax.quantize(Decimal(10) ** -2).normalize()
        transaction_total = TransactionTotal(total, tax)
        return transaction_total

class LineItem(models.Model):
    transaction = models.ForeignKey(Transaction)
    upc = models.CharField(max_length=30)
    quantity = models.DecimalField(max_digits=15, decimal_places=0)
    scale = models.DecimalField(max_digits=19, decimal_places=4, null=True)
    description = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=17, decimal_places=2)
    item = models.ForeignKey('inventory.Item')

    def __unicode__(self):
        return str(self.scale) + ' x ' + self.description + ' ' + self.description

    def total(self):
        return self.price * self.quantity

class TransactionTotal():
    def __init__(self, sub_total, tax_total):
        self.sub_total = sub_total
        self.tax_total = tax_total
        self.total = sub_total + tax_total