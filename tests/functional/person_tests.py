from django.test import TestCase
from account.models import Person, Account, Role, Group

class MockRequest:
    def __init__(self):
        self.session = {}

class PersonTests(TestCase):
    fixtures = [
        'test/accounts.json', 
        'test/people.json', 
        'test/groups.json', 
        'test/roles.json',
    ]
    
    def setUp(self):
        self.person_one = Person.objects.get(username = 'snhorne')
        admin_role=Role.objects.get(name='admin')
        admin_guest=Role.objects.get(name='guest')
        self.person_one.role_set.add(admin_role)
        self.person_one.role_set.add(admin_guest)

        
    def test_roles(self):
        assert len(self.person_one.roles) == 2
        assert 'admin' in self.person_one.roles
        assert 'guest' in self.person_one.roles
        
    def test_has_admin_role(self):
        self.assertTrue(
            self.person_one.has_roles('admin&guest')
        )
        
    def test_can_be_destroyed(self):
        assert self.person_one.can_be_destroyed()
        self.person_one.add_role('account_admin')
        assert not self.person_one.can_be_destroyed()
        
        
        
        
    def test_has_not_super_admin_role(self):
        self.assertFalse(
            self.person_one.has_roles('(admin|guest)&superadmin')
        )
    
    def test_check_password(self):
        self.assertTrue(
            self.person_one.check_password('password')
        )
        
    def test_set_password(self):
        self.person_one.set_password('secret')
        self.assertTrue(
            self.person_one.check_password('secret')
        )
        self.assertFalse(
            self.person_one.check_password('password')
        )
        
    def test_check_password(self):
        self.assertTrue(
            self.person_one.check_password('password')
        )
    
    def test_reset_password(self):
        new_password = self.person_one.reset_password(10)
        self.assertEqual(
            len(new_password),
            10
        )
        self.assertTrue(
            self.person_one.check_password(new_password)
        )
        
    def test_authenticate(self):
        self.assertEquals(
            Person.authenticate(
                'snhorne',
                self.person_one.account,
                'password',
            ),
            self.person_one
        )
        
    def test_authenticate_bad(self):
        self.assertEquals(
            Person.authenticate(
                'snhorne',
                self.person_one.account,
                'wrongpassword',
            ),
            None
        )
        
    def test_login_logout(self):
        request = MockRequest()
        self.person_one.login(request)
        # Person will be saved to request
        self.assertEquals(
            request.person,
            self.person_one,
        )
        # Person's id will be saved to session
        self.assertEquals(
            request.session[Person.SESSION_KEY],
            self.person_one.id,
        )
        
        # On logout these are cleared.
        Person.logout(request)
        
        self.assertEquals(
            request.person,
            None,
        )
        self.assertFalse(
            Person.SESSION_KEY in request.session,
        )
        
    def test_get_user_from_session(self):
        """
        Loads the user with id = request.session[Person.SESSION_KEY]
        """
        request = MockRequest()
        request.account = self.person_one.account
        self.person_one.login(request)
        self.assertEquals(
            Person.load_from_request(request),
            self.person_one,
        )
    
    def test_get_user_from_session_with_no_session_key(self):
        """
        Try to load person from session when ther is no session key
        """
        request = MockRequest()
        request.account = self.person_one.account
        self.assertEquals(
            Person.load_from_request(request),
            None,
        )
        
    def test_get_user_from_session_with_invalid_session_key(self):
        """
        Try to load person from session when the session key
        doesn't match any person's id.
        """
        request = MockRequest()
        request.account = self.person_one.account
        request.session[Person.SESSION_KEY] = 100
        self.assertEquals(
            Person.load_from_request(request),
            None,
        )
