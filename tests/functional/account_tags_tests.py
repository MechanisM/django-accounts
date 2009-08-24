from django.test import Client, TestCase
from django.template import Template, Context
from account.models import Account, Person
from account.tests.mocks import subscription_levels

class AccountTagsTests(TestCase):
        
    fixtures = [
        'test/accounts.json', 
        'test/people.json', 
        'test/groups.json', 
        'test/roles.json',
    ]
    
    def admin_context(self):
        return Context({
            'person': Person.objects.get(pk=2),
            'account': Account.objects.get(pk=1),
        })
    
    def person_context(self):
        return Context({
            'person': Person.objects.get(pk=1),
            'account': Account.objects.get(pk=1),
        })
    
    def has_role(self, role, context):
        t = Template("{%% ifrole %s %%}PASS{%% endifrole %%}" % role)
        return t.render(context) == 'PASS'
    
    def has_group(self, group, context):
        t = Template("{%% ifgroup %s %%}PASS{%% endifgroup %%}" % group)
        return t.render(context) == 'PASS'
    
    def has_level(self, level, context):
        t = Template("{%% iflevel %s %%}PASS{%% endiflevel %%}" % level)
        return t.render(context) == 'PASS'
    
    def has_level_min(self, level, context):
        t = Template("{%% iflevelmin %s %%}PASS{%% endiflevelmin %%}" % level)
        return t.render(context) == 'PASS'
    
    def has_resource(self, resource, context):
        t = Template("{%% ifresource %s %%}PASS{%% endifresource %%}" % resource)
        return t.render(context) == 'PASS'
        
        
    def test_role_tag(self):
        assert self.has_role(
            'account_admin',
            self.admin_context()
        )
        assert not self.has_role(
            'nonexistantrole',
            self.admin_context()
        )
        assert not self.has_role(
            'account_admin',
            self.person_context()
        )
        assert not self.has_role(
            'employee',
            self.person_context()
        )
        
        p = Person.objects.get(pk=1)
        p.add_role('employee', 'consultant')
        p.save()
        assert self.has_role(
            'employee',
            self.person_context()
        )
        assert self.has_role(
            'consultant',
            self.person_context()
        )
        assert self.has_role(
            '"employee | consultant"',
            self.person_context()
        )
        assert self.has_role(
            '"employee & consultant"',
            self.person_context()
        )
        assert self.has_role(
            '"(employee & consultant) | notarole"',
            self.person_context()
        )
        assert not self.has_role(
            '"(employee | consultant) & notarole"',
            self.person_context()
        )
        
        
    def test_group_tag(self):
        assert self.has_group(
            'Admins',
            self.admin_context()
        )
        assert self.has_group(
            'admins',
            self.admin_context()
        )
        assert not self.has_group(
            'notarealgroup',
            self.admin_context()
        )
        assert not self.has_group(
            'admins',
            self.person_context()
        )
        
    def test_subscription_level(self):
        assert self.has_level(
            'silver',
            self.admin_context()
        )
        assert not self.has_level(
            'gold',
            self.admin_context()
        )
        assert not self.has_level(
            'free',
            self.admin_context()
        )
        assert self.has_level_min(
            'silver',
            self.admin_context()
        )
        assert self.has_level_min(
            'free',
            self.admin_context()
        )
        assert not self.has_level_min(
            'gold',
            self.admin_context()
        )


    def test_resource(self):
        # the account checked has a "silver"
        # level as defined in /mocks/subscription_levels.py
        assert not self.has_resource(
            'ssl',
            self.admin_context()
        )
        assert not self.has_resource(
            'projects',
            self.admin_context()
        )
        assert not self.has_resource(
            'disk',
            self.admin_context()
        )
        assert self.has_resource(
            'chat',
            self.admin_context()
        )






