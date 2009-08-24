from django.test import Client, TestCase
from django.contrib.auth.models import User
from account.models import Account
from account import subscription
from django.conf import settings
from account.tests.mocks import subscription_levels

class AccountTests(TestCase):
        
        
    def make_account(self, level=1, people=1):
        """
        Utility method: creates an account with
        a specific subscription level and # people
        """
        account = Account(
            subscription_level_id = level,
        )
        account.save()
        for i in range(people):
            account.person_set.create(
                username = 'person %i' % i,
                password = 'password %i' % i,
                first_name = 'first_name %i' % i,
                last_name = 'last_name %i' % i,
                email = 'email_%i@email.com' % i,
            )
        return account
        
    
    def test_silver_subscription_level(self):
        """
        Tests one of the subscription levels defined
        in setUp()
        """
        account = self.make_account(level = 1, people = 2)
        assert account.subscription_level == settings.SUBSCRIPTION_LEVELS[1]
        assert not account.has_resource('ssl')
        assert not account.has_resource('disk')
        assert not account.has_resource('projects')
        assert account.has_resource('people')
        assert account.has_level('silver') 
        assert account.has_level_or_greater('free') 
        assert account.has_level_or_greater('silver') 
        assert account.requires_payment()
        
        
    def test_gold_subscription_level(self):
        """
        Tests one of the subscription levels defined
        in setUp()
        """
        account = self.make_account(level = 2, people = 10)
        assert account.subscription_level == settings.SUBSCRIPTION_LEVELS[2]
        assert account.has_resource('ssl')
        assert account.has_resource('disk')
        assert account.has_resource('projects')
        assert not account.has_resource('people')
        assert account.has_level('gold') 
        assert account.has_level_or_greater('free') 
        assert account.has_level_or_greater('silver') 
        assert account.has_level_or_greater('gold') 
        assert account.requires_payment()
        
  
        