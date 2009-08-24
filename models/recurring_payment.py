from datetime import date, timedelta, datetime
from django.db import models
from django.conf import settings
from account.lib import payment
from accounts import Account

# gateway = getattr(payment, settings.PAYMENT_GATEWAY)

class RecurringPayment(models.Model):
    class Admin:
        pass
    
    class Meta:
        app_label = 'account'
        
    name = models.CharField(
        max_length = 100,
    )
    number = models.CharField(
        max_length = 20,
    )
    amount = models.CharField(
        max_length = 10,
    )
    
    period = models.IntegerField(
    )
    
    token = models.CharField(
        max_length = 64,
    )
    
    gateway_token = models.CharField(
        max_length = 64,
    )
    
    account = models.ForeignKey(
        to = Account, 
        related_name = 'recurring_payment_set',
        unique = True
    )
    
    cancelled_at = models.DateTimeField(
        blank = True,
        null = True,
    )
    
    created_on = models.DateField(
        auto_now_add = True,
    )
    active_on = models.DateField(
    )
    
    def save(self, *args, **kwargs):
        if not self.active_on:
            self.active_on = date.today()
        if self.account and not self.account.active:
            self.account.active = True
            self.account.save()
        super(RecurringPayment, self).save(*args, **kwargs)
    
    @classmethod
    def create(cls, account, amount, card_number, card_expires, first_name, last_name, period=1, start_date=None,**kwargs):
        
        token = str(account.id)
        amount = str(amount)        
        amount = amount[:-2] + '.' + amount[-2:]
        '''
        gateway_token = gateway.start_payment(
            url = settings.PAYMENT_GATEWAY_URL,
            login = settings.PAYMENT_GATEWAY_LOGIN,
            password = settings.PAYMENT_GATEWAY_PASSWORD,
            token = token,
            amount = amount,
            card_number = card_number,
            card_expires = card_expires.strftime('%Y-%m'),
            first_name = first_name,
            last_name = last_name,
            period = period, 
            **kwargs
        )
        
        obj = cls(
            account = account,
            number = '*' * (len(card_number)-4) + card_number[-4:],
            name = ' '.join([first_name, last_name]),
            amount = '$' + amount,
            period = period,
            gateway_token = gateway_token,
            token = token,
            active_on = start_date or date.today(),
        )
        '''
        return obj
        
    def change_amount(self, amount, **kwargs):
        amount = str(amount)
        gateway.change_payment(
            url = settings.PAYMENT_GATEWAY_URL,
            login = settings.PAYMENT_GATEWAY_LOGIN,
            password = settings.PAYMENT_GATEWAY_PASSWORD,            
            amount = amount[:-2] + '.' + amount[-2:],
            gateway_token = self.gateway_token,
            **kwargs
        )
        self.amount = '$' + amount
        
    def cancel(self, **kwargs):
        gateway.cancel_payment(
            url = settings.PAYMENT_GATEWAY_URL,
            login = settings.PAYMENT_GATEWAY_LOGIN,
            password = settings.PAYMENT_GATEWAY_PASSWORD,            
            gateway_token = self.gateway_token,
            **kwargs
        )
        self.deactivate()
        
    
    def deactivate(self):
        self.cancelled_at = datetime.now()
        
        
    def is_active(self):
        return not self.cancelled_at
        
    def is_expired(self, when=None):
        if not self.cancelled_at:
            return False
        
        return self.final_payment() < (when or datetime.now())
            
    def final_payment(self):
        if not self.is_active():
            return self.next_payment(self.cancelled_at)
        
    def next_payment(self, after = None):
        from dateutil.rrule import rrule, MONTHLY
        return rrule(
            MONTHLY, 
            dtstart = self.active_on,
            interval = self.period,
        ).after(after or datetime.now())
        
        
    
    
    
    
    
    
    
    
    
    
    
    
