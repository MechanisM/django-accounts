from django.conf import settings
from account import subscription
from account.models import Account

settings.SUBSCRIPTION_LEVELS = (
    {
        'handle': 'free',
        'name': 'Free Membership',
        'description': 'The free membership is for...',
        'price': 0,
        'resources': {
            'people': 10,
            'disk': 1000,
            'chat': True,
            'ssl': True,
            'projects': 0,
        }
    },
    {
        'handle': 'silver',
        'name': 'Silver Membership',
        'description': 'The silver membership is for...',
        'price': 10000,
        'period': 1,
        'trial': 1,
        'resources': {
            'people': 10,
            'disk': 1000,
            'chat': True,
            'ssl': False,
            'projects': 0,
        }
    },
    {
        'handle': 'gold',
        'name': 'Gold Membership',
        'description': 'The gold membership is for...',
        'price': 20000,
        'period': 1,
        'trial': 1,
        'resources': {
            'people': 10,
            'disk': 10000,
            'chat': True,
            'ssl': True,
            'projects': subscription.Unlimited,
        }
    },
    
    
)

settings.SUBSCRIPTION_REGULATORS = {
    'people': subscription.count('account', 'Person'),
    'disk': subscription.class_method('account', 'Account', 'disk_used'),
    'projects': subscription.class_method('account', 'Account', 'projects_count')
}   
Account.disk_used = lambda a: 1000
Account.projects_count = lambda a: 65535
    
