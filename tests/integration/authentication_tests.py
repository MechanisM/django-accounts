import re
from django.test import TestCase, Client
from django.core import mail
from account.models import Person, Account
from base import IntegrationTest
import django.newforms as forms
import causes
import effects
import security

LOGIN_PATH = '/person/login/'
LOGOUT_PATH = '/person/logout/'
RESET_PATH = '/person/reset_password/'
CHANGE_PASSWORD_PATH = '/person/change_password/1/'
CHANGE_PASSWORD_PATH_MISMATCH = '/person/change_password/3/'
CHANGE_PASSWORD_PATH_INVALID = '/person/change_password/999/'
CHANGE_OWN_PASSWORD_PATH = '/person/change_password/'

    
class AuthenticationTests(IntegrationTest):
    fixtures = ['test/accounts.json', 'test/people.json']
    
    def test_login(self):
        """
        Tests for person_views.login
        """
        
        #-------------------------------------------------
        # If ssl is not on for GET, redirect to ssl page
        #-------------------------------------------------
        self.assertState(
            'GET',
            LOGIN_PATH,
            [
                causes.valid_domain,
            ],
            [
                effects.redirected(LOGIN_PATH, status = 301, ssl = True)
            ]
        )
        #-------------------------------------------------
        # If ssl is not on for POST, 403 Forbidden
        #-------------------------------------------------
        self.assertState(
            'POST',
            LOGIN_PATH,
            [
                causes.valid_domain,
            ],
            [
                effects.status(403)
            ]
        )        
        
        
        self.assertState(
            'GET/POST',
            LOGIN_PATH,
            [
                causes.ssl,
                causes.person_not_logged_in,
                causes.valid_domain,
                causes.no_login_parameters,
            ],
            [
                effects.not_logged_in,
                effects.rendered('account/login_form.html'),
                effects.status(200),
            ]
        )
    
        self.assertState(
            'GET/POST',
            LOGIN_PATH,
            [
                causes.ssl,
                causes.person_not_logged_in,
                causes.invalid_domain,
            ],
            [
                effects.not_logged_in,
                effects.status(404),
            ]
        )
    
        self.assertState(
            'GET/POST',
            LOGIN_PATH,
            [
                causes.ssl,
                causes.person_not_logged_in,
                causes.no_domain,
            ],
            [
                effects.not_logged_in,
                effects.status(404),
            ]
        )
    
        self.assertState(
            'GET/POST',
            LOGIN_PATH,
            [
                causes.ssl,
                causes.person_logged_in,
                causes.valid_domain,
            ],
            [
                effects.logged_in,
                effects.status(403),
            ]
        )
    
        self.assertState(
            'POST',
            LOGIN_PATH,
            [
                causes.ssl,
                causes.person_not_logged_in,
                causes.valid_domain,
                causes.valid_login_parameters,
                causes.remember_me_not_checked,
            ],
            [
                effects.logged_in,
                effects.redirected('/'),
                effects.logged_in, # Make sure we're still logged in after redirect.
                effects.session_expires_on_close,
            ]
        )
    
        self.assertState(
            'POST',
            LOGIN_PATH,
            [
                causes.ssl,
                causes.person_not_logged_in,
                causes.valid_domain,
                causes.valid_login_parameters,
                causes.account_inactive,
            ],
            [
                effects.logged_in,
                effects.redirected('/account/inactive/'),
            ]
        )
        
        self.assertState(
            'POST',
            LOGIN_PATH,
            [
                causes.ssl,
                causes.person_not_logged_in,
                causes.valid_domain,
                causes.valid_admin_login_parameters,
                causes.account_inactive,
            ],
            [
                effects.person_logged_in(pk = 2),
                effects.redirected('/account/change_payment_method/'),
            ]
        )
    
        self.assertState(
            'POST',
            LOGIN_PATH,
            [
                causes.ssl,
                causes.person_not_logged_in,
                causes.valid_domain,
                causes.valid_login_parameters,
                causes.remember_me_checked,
                causes.account_active,
            ],
            [
                effects.logged_in,
                effects.redirected('/'),
                effects.logged_in,
                effects.session_persists_after_close,
            ]
        )
    
        self.assertState(
            'POST',
            LOGIN_PATH,
            [
                causes.ssl,
                causes.person_not_logged_in,
                causes.valid_domain,
                causes.invalid_login_parameters,
                causes.account_active,
            ],
            [
                effects.not_logged_in,
                effects.rendered('account/login_form.html'),
                effects.status(200),
            ]
        )
    
        self.assertState(
            'GET/POST',
            LOGIN_PATH,
            [
                causes.ssl,
                causes.person_logged_in,
                causes.mismatched_domain,
                causes.no_login_parameters,
                causes.account_active,
            ],
            [
                effects.not_logged_in,
                effects.rendered('account/login_form.html'),
                effects.status(200),
            ]
        )
    
    
    def test_logout(self):
        """
        Tests for person_views.logout
        """
        self.assertState(
            'GET/POST',
            LOGOUT_PATH,
            [
                causes.person_not_logged_in,
                causes.invalid_domain,
            ],
            [
                effects.not_logged_in,
                effects.status(404),
            ]
        )
        self.assertState(
            'GET/POST',
            LOGOUT_PATH,
            [
                causes.person_not_logged_in,
                causes.no_domain,
            ],
            [
                effects.status(404),
            ]
        )
        self.assertState(
            'GET/POST',
            LOGOUT_PATH,
            [
                causes.person_not_logged_in,
                causes.valid_domain,
            ],
            [
                effects.not_logged_in,
                effects.redirected(LOGIN_PATH, ssl=True),
            ]
        )
        self.assertState(
            'POST',
            LOGOUT_PATH,
            [
                causes.person_logged_in,
                causes.valid_domain,
            ],
            [
                effects.not_logged_in,
                effects.redirected(LOGIN_PATH, ssl=True),
            ]
        )
        self.assertState(
            'GET',
            LOGOUT_PATH,
            [
                causes.person_logged_in,
                causes.valid_domain,
            ],
            [
                effects.logged_in,
                effects.status(405),
            ]
        )
    
    
    def test_reset_password(self):
        """
        Tests for person_views.reset_password
        """
        def email_contains_password(client, response, testcase):
            """ Checks that the password of the default user is in 
            the first email in the outbox. """
        
            person = Person.objects.get(username = 'snhorne')
            self.assertEqual(
                mail.outbox[0].to,
                [person.email],
            )
            pattern = re.compile('assword: *(.{7})\n')
            matches = pattern.search(mail.outbox[0].body)
            new_password = matches.group(1)
        
            testcase.assertTrue(
                person.check_password(new_password)
            )
            
        self.assertState(
            'GET/POST',
            RESET_PATH,
            [
                causes.person_not_logged_in,
                causes.invalid_domain,
            ],
            [
                effects.status(404),
            ]
        )
        
        self.assertState(
            'GET/POST',
            RESET_PATH,
            [
                causes.person_logged_in,
                causes.valid_domain,
            ],
            [
                effects.status(403),
            ]
        )
        self.assertState(
            'GET',
            RESET_PATH,
            [
                causes.person_not_logged_in,
                causes.valid_domain,
            ],
            [
                effects.rendered('account/reset_password_form.html'),
                effects.status(200),
            ]
        )
        self.assertState(
            'POST',
            RESET_PATH,
            [
                causes.person_not_logged_in,
                causes.valid_domain,
                causes.invalid_username,
            ],
            [
                effects.outbox_len(0),
                effects.rendered('account/reset_password_form.html'),
            ]
        )
        self.assertState(
            'POST',
            RESET_PATH,
            [
                causes.person_not_logged_in,
                causes.valid_domain,
                causes.valid_username,
            ],
            [
                effects.outbox_len(1),
                email_contains_password,
                effects.rendered('account/reset_password_success.html'),
                effects.status(200),
            ]
        )
        

    
    #def test_change_password(self):
        #"""
        #Tests for authentication.change_password
        #"""
        #security.check(self, CHANGE_PASSWORD_PATH, causes.ssl)
        #self.assertState(
            #'GET',
            #CHANGE_PASSWORD_PATH,
            #[
                #causes.ssl,
                #causes.owner_logged_in,
                #causes.valid_domain,
            #],
            #[
                #effects.rendered('account/change_password_form.html'),
                #effects.context('form', type = forms.BaseForm),
                #effects.status(200),
            #]
        #)
        #self.assertState(
            #'GET/POST',
            #CHANGE_PASSWORD_PATH_INVALID,
            #[
                #causes.ssl,
                #causes.owner_logged_in,
                #causes.valid_domain,
            #],
            #[
                #effects.status(404),
            #]
        #)
        #self.assertState(
            #'GET/POST',
            #CHANGE_PASSWORD_PATH_MISMATCH,
            #[
                #causes.ssl,
                #causes.owner_logged_in,
                #causes.valid_domain,
            #],
            #[
                #effects.status(404),
            #]
        #)
            
        #self.assertState(
            #'POST',
            #CHANGE_PASSWORD_PATH,
            #[
                #causes.ssl,
                #causes.owner_logged_in,
                #causes.valid_domain,
                #causes.params(
                    #password = 'newpassword',
                    #password2 = 'mismatch',
                #)
            #],
            #[
                #effects.rendered('account/change_password_form.html'),
                #effects.context('form', type = forms.BaseForm),
                #effects.form_errors('form'),
                #effects.status(200),
            #]
        #)
        
            
        #def password_was_changed(client, response, testcase):
            #person = Person.objects.get(pk = 1)
            #assert person.check_password == 'bob'
    
        #self.assertState(
            #'POST',
            #CHANGE_PASSWORD_PATH,
            #[
                #causes.ssl,
                #causes.alters(Person),
                #causes.owner_logged_in,
                #causes.valid_domain,
                #causes.params(
                    #password = 'newpassword',
                    #password2 = 'newpassword',
                #)
            #],
            #[
                #effects.person_has_password(1, 'newpassword'),
                #effects.redirected('/person/edit/1/'),
            #]
        #)
            
        #self.assertState(
            #'GET/POST',
            #'/person/change_password/3/',
            #[
                #causes.ssl,
                #causes.alters(Person),
                #causes.owner_logged_in,
                #causes.valid_domain,
            #],
            #[
                #effects.status(404),
            #]
        #)
            
        
