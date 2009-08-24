from django.test import TestCase
from account.models import Person, Account, Role, Group

class MockRequest:
    def __init__(self):
        self.session = {}

class GroupTests(TestCase):
    fixtures = [
        'test/accounts.json', 
        'test/people.json', 
        'test/groups.json', 
        'test/roles.json',
    ]
    
    def setUp(self):
        self.person_one = Person.objects.get(username = 'snhorne')
        
    def test_person_get_role_from_group(self):
        """
        A person belonging to a group will inherit
        all of the groups roles, in addition to his
        own. 
        """
        self.person_one.role_set.add(Role.objects.get(name='admin'))
        self.assertFalse(
            self.person_one.has_roles('employee')
        )
        self.person_one.group = Group.objects.get(name = 'Employees')
        self.assertTrue(
            self.person_one.group.has_roles('employee')
        )
        self.assertTrue(
            self.person_one.has_roles('employee')
        )
        self.assertTrue(
            self.person_one.has_roles('admin')
        )
        self.person_one.group = None
        self.assertFalse(
            self.person_one.has_roles('employee')
        )
    
    def test_duplicate_name(self):
        account = Account.objects.get(pk=1)
        g1 = Group(account = account, name = "samenamegame")
        g1.save()
        g2 = Group(account = account, name = "samenamegame")
        try:
            g2.save()
            raise False
        except:
            # It seems that the exception raised is DB specific.
            # So we just catch all exceptions here. 
            pass
        
        
        
        
        
        
        
        
        
        
        
