from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from account import subscription

class Account(models.Model):
    
    class Admin:
        pass
    
    class Meta:
        app_label = 'account'
        unique_together = (
            ("subdomain", "domain"),
        )
    
    subdomain = models.CharField(
        verbose_name = "Sub-domain",
        max_length = 50,
    )
    
    domain = models.CharField(
        verbose_name = "Domain Name",
        max_length = 150,
        choices = settings.ACCOUNT_DOMAINS,
    )
    
    timezone = models.CharField(
        max_length = 50,
        default = 'utc',
        choices = settings.ACCOUNT_TIME_ZONES,
    )
    
    name = models.CharField(
        verbose_name = "Account Name",
        max_length = 40,
    )
    
    
    created_on = models.DateTimeField(
        auto_now_add = True,
    )
    
    active = models.BooleanField(
        default = True,
        blank = True,
    )
    
    website = models.URLField(
        verify_exists = True,
        blank = True,
    )
    
    # Stupid django bug alert. Django will think 
    # that no value has been passed if the value is 0
    subscription_level_id = models.IntegerField(
        default = 0,
        blank = True,
    )   
    
        
        
    @property
    def full_domain(self):
        return "%s.%s" % (self.subdomain, self.domain)
    
    def _get_recurring_payment(self):
        """
        This is a hack to avoid 1-to-1 relationship, since that
        will supposedly be changing soon. Is there a better way
        to do this?
        """
        try:
            return self.recurring_payment_set.all()[0]
        except IndexError:
            return None
        
    def _set_recurring_payment(self, value):
        self.recurring_payment_set.add(value)        
        
    recurring_payment = property(_get_recurring_payment, _set_recurring_payment)
        
    @property
    def subscription_level(self):
        return settings.SUBSCRIPTION_LEVELS[self.subscription_level_id]
    
    def _find_level(self, handle):
        for i, level in enumerate(settings.SUBSCRIPTION_LEVELS):
            if level['handle'] == handle:
                return i, level
        
    def requires_payment(self):
        return self.subscription_level['price'] > 0
            
    def has_level_or_greater(self, handle):
        i, level = self._find_level(handle)
        return self.subscription_level_id >= i
            
    def has_level(self, handle):
        i, level = self._find_level(handle)
        return self.subscription_level_id == i
            
            
        
    def has_resource(self, resource_name):
        if not resource_name:
            return True
        resource = self.subscription_level['resources'][resource_name]
        if resource is subscription.Unlimited:
            return True
        return settings.SUBSCRIPTION_REGULATORS.get(resource_name, lambda a, v: v)(
            self,
            resource
        )

    
    def __unicode__(self):
        return self.name

    @classmethod
    def load_from_request(cls, request):
        try:
            pieces = request.META['HTTP_HOST'].split('.')
            request.account = Account.objects.get(
                subdomain = pieces[0],
                domain = '.'.join(pieces[1:]),
            )
        except (models.ObjectDoesNotExist, KeyError):
            request.account = None
        
        return request.account
        
        
