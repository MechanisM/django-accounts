import re
from django.test import TestCase, Client
from django.core import mail
from account.models import Person, Account
import django.newforms as forms
from base import IntegrationTest
import security
import causes
import effects

LIST_PATH = '/person/list/'
CREATE_PATH = '/person/create/'
EDIT_SELF_PATH = '/person/'
EDIT_PATH = '/person/edit/1/'
EDIT_PATH_INVALID = '/person/edit/999/'
EDIT_PATH_MISMATCH = '/person/edit/3/'

DESTROY_PATH = '/person/destroy/1/'
DESTROY_PATH_INVALID = '/person/destroy/999/'
DESTROY_PATH_OWNER = '/person/destroy/2/'
DESTROY_PATH_MISMATCH = '/person/destroy/3/'

create_person_parameters = {
    'username': 'bob_jones',
    'new_password': 'password',
    'new_password_confirm': 'password',
    'first_name': 'bob',
    'last_name': 'jones',
    'email': 'bob@email.com',
}
create_person_parameters_without_password = {
    'username': 'bob_jones',
    'new_password': '',
    'new_password_confirm': '',
    'first_name': 'bob',
    'last_name': 'jones',
    'email': 'bob@email.com',
}
    
class ProfileTests(IntegrationTest):
    fixtures = [
        'test/accounts.json', 
        'test/people.json', 
        'test/groups.json', 
        'test/roles.json',
    ]    
    def test_list(self):
        """
        Tests for profile.list
        """
        def people_match_account(client, response, testcase):
            # client.previous_request is only available
            # in patched test client.
            if hasattr(client, 'previous_request'):
                people = response.context[0]['object_list']           
                expected = Person.objects.filter(account = client.previous_request.account)
                assert len(people) == len(expected)
                for p in people:
                    assert p in expected
            
            
        security.check(self, LIST_PATH)
        
        #-------------------------------------------------
        # The list is displayed.
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            LIST_PATH,
            [
                causes.owner_logged_in,
                causes.valid_domain,
            ],
            [
                people_match_account,
                effects.rendered('account/person_list.html'),
                effects.status(200),
            ]
        )
    
    def test_create(self):
        """
        Tests for profile.create
        """
        security.check(self, CREATE_PATH, causes.ssl)
        
        #-------------------------------------------------
        # The person form is displayed
        #-------------------------------------------------
        self.assertState(
            'GET',
            CREATE_PATH,
            [
                causes.ssl,
                causes.owner_logged_in,
                causes.valid_domain,
            ],
            [
                effects.rendered('account/person_form.html'),
                effects.context('form', type = forms.BaseForm),
                effects.status(200),
            ]
        )
        #-------------------------------------------------
        # If input errors, the person form is displayed
        #-------------------------------------------------
        self.assertState(
            'POST',
            CREATE_PATH,
            [
                causes.ssl,
                causes.owner_logged_in,
                causes.valid_domain,
                causes.invalid_create_person_parameters,
            ],
            [
                effects.rendered('account/person_form.html'),
                effects.context('form', type = forms.BaseForm),
                effects.form_errors('form'),
                effects.status(200),
            ]
        )        #-------------------------------------------------
        # Password is required for create.
        #-------------------------------------------------
        self.assertState(
            'POST',
            CREATE_PATH,
            [
                causes.ssl,
                causes.owner_logged_in,
                causes.valid_domain,
                causes.params(**create_person_parameters_without_password),
            ],
            [
                effects.rendered('account/person_form.html'),
                effects.context('form', type = forms.BaseForm),
                effects.form_errors('form'),
                effects.status(200),
            ]
        )        #-------------------------------------------------
        # If everything is valid, create the person
        #-------------------------------------------------
        self.assertState(
            'POST',
            CREATE_PATH,
            [
                causes.ssl,
                causes.alters(Person),
                causes.owner_logged_in,
                causes.valid_domain,
                causes.params(**create_person_parameters),
            ],
            [
                effects.created(Person),
                effects.redirected('/person/list/'),
            ]
        )
        person = Person.objects.get(username = 'bob_jones')
        assert person.check_password('password')
    
    
    def test_edit(self):
        security.check(self, EDIT_PATH)
        
        #-------------------------------------------------
        # Show the form
        #-------------------------------------------------
        self.assertState(
            'GET',
            EDIT_PATH,
            [
                causes.owner_logged_in,
                causes.valid_domain,
            ],
            [
                effects.rendered('account/person_form.html'),
                effects.context('form', type = forms.BaseForm),
                effects.status(200),
            ]
        )
        #-------------------------------------------------
        # If the person does not exist, 404
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            EDIT_PATH_INVALID,
            [
                causes.owner_logged_in,
                causes.valid_domain,
            ],
            [
                effects.status(404),
            ]
        )
        #-------------------------------------------------
        # If the person does not belong to the account 404
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            EDIT_PATH_MISMATCH,
            [
                causes.owner_logged_in,
                causes.valid_domain,
            ],
            [
                effects.status(404),
            ]
        )
        #-------------------------------------------------
        # If invalid input, show form
        #-------------------------------------------------
        self.assertState(
            'POST',
            EDIT_PATH,
            [
                causes.owner_logged_in,
                causes.valid_domain,
                causes.invalid_create_person_parameters,
            ],
            [
                effects.rendered('account/person_form.html'),
                effects.context('form', type = forms.BaseForm),
                effects.form_errors('form'),
                effects.status(200),
            ]
        )
        
        #-------------------------------------------------
        # If valid, save changes
        #-------------------------------------------------
        self.assertState(
            'POST',
            EDIT_PATH,
            [
                causes.alters(Person),
                causes.owner_logged_in,
                causes.valid_domain,
                causes.params(
                    username = 'bob_jones',
                    new_password = '',
                    new_password_confirm = '',
                    first_name = 'bob',
                    last_name = 'jones',
                    email = 'bob@email.com',
                ),
            ],
            [
                effects.field_value(Person, {'pk':1}, first_name = 'bob'),
                effects.person_has_password(1, 'password'),
                effects.redirected('/person/list/'),
            ]
        )
        
        #-------------------------------------------------
        # If valid, save changes
        #-------------------------------------------------
        self.assertState(
            'POST',
            EDIT_PATH,
            [
                causes.alters(Person),
                causes.owner_logged_in,
                causes.valid_domain,
                causes.params(
                    username = 'bob_jones',
                    new_password = 'anewpassword',
                    new_password_confirm = 'anewpassword',
                    first_name = 'bob',
                    last_name = 'jones',
                    email = 'bob@email.com',
                ),
            ],
            [
                effects.person_has_password(1, 'anewpassword'),
                effects.field_value(Person, {'pk':1}, first_name = 'bob'),
                effects.redirected('/person/list/'),
            ]
        )
        #-------------------------------------------------
        # Edit does not require pasword, does not change
        # if one is not provided.
        #-------------------------------------------------
        self.assertState(
            'POST',
            EDIT_PATH,
            [
                causes.alters(Person),
                causes.owner_logged_in,
                causes.valid_domain,
                causes.params(
                    username = 'bob_jones',
                    new_password = '',
                    new_password_confirm = '',
                    first_name = 'bob',
                    last_name = 'jones',
                    email = 'bob@email.com',
                ),
            ],
            [
                effects.person_has_password(1, 'anewpassword'),
                effects.field_value(Person, {'pk':1}, first_name = 'bob'),
                effects.redirected('/person/list/'),
            ]
        )
        #-------------------------------------------------
        # If passwords didn't match, show form
        #-------------------------------------------------
        self.assertState(
            'POST',
            EDIT_PATH,
            [
                causes.alters(Person),
                causes.owner_logged_in,
                causes.valid_domain,
                causes.params(
                    username = 'bob_jones',
                    new_password = 'password',
                    new_password_confirm = 'does_not_match',
                    first_name = 'bob',
                    last_name = 'jones',
                    email = 'bob@email.com',
                ),
            ],
            [
                effects.rendered('account/person_form.html'),
                effects.context('form', type = forms.BaseForm),
                effects.form_errors('form'),
                effects.status(200),
            ]
        )
    
    
    def test_edit_self(self):        #-------------------------------------------------
        # You have to be logged in to edit yourself 
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            EDIT_SELF_PATH,
            [
                causes.person_not_logged_in,
                causes.valid_domain,
            ],
            [
                effects.redirected('/person/login/', ssl = True),
            ]
        )
        
        #-------------------------------------------------
        # You have to be using an account to edit yourself.
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            EDIT_SELF_PATH,
            [
                causes.invalid_domain,
            ],
            [
                effects.status(404)
            ]
        )
        #-------------------------------------------------
        # Show the form 
        #-------------------------------------------------
        self.assertState(
            'GET',
            EDIT_SELF_PATH,
            [
                causes.person_logged_in,
                causes.valid_domain,
            ],
            [
                effects.rendered('account/person_form.html'),
                effects.context('form', type = forms.BaseForm),
                effects.status(200),
            ]
        )
        #-------------------------------------------------
        # Submitting invalid data shows the form 
        #-------------------------------------------------
        self.assertState(
            'POST',
            EDIT_SELF_PATH,
            [
                causes.person_logged_in,
                causes.valid_domain,
                causes.params(
                    first_name = 'mary',
                    last_name = 'sue',
                    email = '---',
                ),

            ],
            [
                effects.rendered('account/person_form.html'),
                effects.context('form', type = forms.BaseForm),
                effects.status(200),
            ]
        )
        #-------------------------------------------------
        # Submitting valid data changes the record. 
        # But if you're not an admin, you can't edit your roles.
        #-------------------------------------------------
        self.assertState(
            'POST',
            EDIT_SELF_PATH,
            [
                causes.person_logged_in,
                causes.valid_domain,
                causes.params(
                    first_name = 'mary',
                    last_name = 'sue',
                    email = 'mary@email.com',
                    role_set = ['1', '13'],
                ),

            ],
            [
                effects.person_has_password(1, 'password'),
                effects.person_does_not_have_role('account_admin', pk=1),
                effects.person_does_not_have_role('consultant', pk=1),
                effects.rendered('account/person_form.html'),
                effects.context('form', type = forms.BaseForm),
                effects.status(200),
            ]
        )
        #-------------------------------------------------
        # Submitting valid data changes the record. 
        # If your're an admin, you CAN edit your roles
        # with the exception that you CAN NOT remove your
        # own admin priveledges.
        #-------------------------------------------------
        self.assertState(
            'POST',
            EDIT_SELF_PATH,
            [
                causes.owner_logged_in,
                causes.valid_domain,
                causes.params(
                    username = "kmnicholson",
                    first_name = 'mary',
                    last_name = 'sue',
                    email = 'mary@email.com',
                    role_set = ['14'],
                ),

            ],
            [
                effects.person_has_password(2, 'password'),
                effects.person_has_role('janitor', pk=2),
                effects.person_has_role('account_admin', pk=2),
                effects.redirected('/person/'),
            ]
        )
        #-------------------------------------------------
        # If the user provides a new password, it will be changed
        #-------------------------------------------------
        self.assertState(
            'POST',
            EDIT_SELF_PATH,
            [
                causes.person_logged_in,
                causes.valid_domain,
                causes.params(
                    username = 'snhorne',
                    first_name = 'starr',
                    last_name = 'horne',
                    email = 'starr@email.com',
                    new_password = 'newone',
                    new_password_confirm = 'newone',
                ),

            ],
            [
                effects.person_has_password(1, 'newone'),
                effects.redirected('/person/'),
            ]
        )
        
        


    def test_destroy(self):
        """
        Tests for profile.destroy
        """
        security.check(self, DESTROY_PATH)
        self.assertState(
            'GET',
            DESTROY_PATH,
            [
                causes.owner_logged_in,
                causes.valid_domain,
            ],
            [
                effects.rendered('account/confirm_destroy.html')
            ]
        )
    
        self.assertState(
            'POST',
            DESTROY_PATH_INVALID,
            [
                causes.owner_logged_in,
                causes.valid_domain,
            ],
            [
                effects.status(404),
            ]
        )
        
        self.assertState(
            'POST',
            DESTROY_PATH_MISMATCH,
            [
                causes.owner_logged_in,
                causes.valid_domain,
            ],
            [
                effects.status(404),
            ]
        )
        
        self.assertState(
            'POST',
            DESTROY_PATH,
            [
                causes.owner_logged_in,
                causes.valid_domain,
            ],
            [
                effects.does_not_exist(Person, id = 1),
                effects.redirected('/person/list/')
            ]
        )
    
        self.assertState(
            'POST',
            DESTROY_PATH_OWNER,
            [
                causes.owner_logged_in,
                causes.valid_domain,
            ],
            [
                effects.exists(Person, id = 2),
                effects.status(403)
                
            ]
        )
    
    
    
    
    
    
    
    
    
    
    