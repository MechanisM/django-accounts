import re
from datetime import timedelta
from datetime import date
from django.test import TestCase, Client
from django.core import mail
from django.conf import settings
from account.models import Person, Account, RecurringPayment
from base import IntegrationTest
import django.newforms as forms
import causes
import effects
import security
from account.tests.mocks.payment_gateway import MockGateway
from account.models import recurring_payment
from account.lib.payment.errors import PaymentRequestError, PaymentResponseError

from account.tests.mocks import subscription_levels
CREATE_PATH = '/account/create/%i/'
UPGRADE_PATH = '/account/upgrade/%i/'
CHANGE_PM_PATH = '/account/change_payment_method/'
CANCEL_PM_PATH = '/account/cancel_payment_method/'
EDIT_ACCOUNT_PATH = '/account/'

    
############################
# Causes and Effects
############################

def payment_request_error(client, request):
    """
    Make the mock payment gateway return a PaymentRequestError
    on create, update or delete payment
    """
    recurring_payment.gateway.error = PaymentRequestError
    return client, request

def payment_response_error(client, request):
    """
    Make the mock payment gateway return a PaymentResponseError
    on create, update or delete payment
    """
    recurring_payment.gateway.error = PaymentResponseError
    return client, request

def payment_response_error_on_cancel(client, request):
    """
    Make the mock payment gateway return a PaymentResponseError
    only on delete payment
    """
    recurring_payment.gateway.reset()
    recurring_payment.gateway.error_on_cancel = PaymentResponseError
    return client, request
        
def gateway_cancel_called(client, response, testcase):
    """ 
    Assert that the mock gateway's cancel payment method was called.
    """
    assert recurring_payment.gateway.cancel_payment_called
    def gateway_start_called(client, response, testcase):
    """ 
    Assert that the mock gateway's start payment method was called.
    """
    assert recurring_payment.gateway.start_payment_called
    def gateway_change_called(client, response, testcase):
    """ 
    Assert that the mock gateway's change payment method was called.
    """
    assert recurring_payment.gateway.change_payment_called
    def payment_is_inactive(client, response, testcase):
    """
    Assert that payment for the first account is inactive.
    """
    assert not RecurringPayment.objects.get(account__pk = 1).is_active()

def payment_is_active(client, response, testcase):
    """
    Assert that payment for the first account is active.
    """
    assert RecurringPayment.objects.get(account__pk = 1).is_active()
    
def subscription_level_is(n):
    def check_subscription_level(client, response, testcase):
        """
        Assert that payment for the first account is active.
        """
        assert Account.objects.get(pk = 1).subscription_level_id == n
    return check_subscription_level
    
def account_has_subscription_level(n):
    def set_subscription_level(client, parameters):
        """
        Set the subscription level for the first acct.
        """
        account = Account.objects.get(pk = 1)
        account.subscription_level_id = n
        account.save()
        return client, parameters
    return set_subscription_level


def account_has_no_payment_method(client, parameters):
    """
    Assert that the first account has no payment method.
    """
    try:
        RecurringPayment.objects.get(account__pk = 1).delete()
    except RecurringPayment.DoesNotExist:
        pass
    return client, parameters

# The start_date for sample RecurringPayment
PAYMENT_START = date(2006, 3, 19)


def account_has_payment_method(client, parameters):
    """
    Create a payment method for the first account.
    """
    account_has_no_payment_method(client, parameters)
    Account.objects.get(pk = 1).recurring_payment = RecurringPayment(
        name = 'Bob Jones',
        period = 1,
        amount = '$10.00',
        number = '********1234',
        token = 2,
        gateway_token = '1000',
        active_on = PAYMENT_START,
    )
    return client, parameters

def account_has_inactive_payment_method(client, parameters):
    account_has_payment_method(client, parameters)
    payment = Account.objects.get(pk = 1).recurring_payment
    payment.deactivate()
    payment.save()
    return client, parameters
    
domain = '%s.%s' % ('billybob', settings.ACCOUNT_DOMAINS[1][0])

def delete_test_account(client, parameters):    """
    Delete the test account created by our Signup tests.
    """
    try:
        Person.objects.get(username = 'billybob').delete()
        Account.objects.get(
            subdomain = signup_params_no_cc['subdomain'],
            domain = signup_params_no_cc['domain']).delete()
    except (Person.DoesNotExist, Account.DoesNotExist):
        pass
    return client, parameters


def new_payment_starts_when_old_one_stops(client, response, testcase):
    """
    Check that when you've changed a credit card, that the new
    card starts being billed when the old one is stopped bein billed.
    """
    new_payment = RecurringPayment.objects.get(account__pk = 1)
    from dateutil.rrule import rrule, MONTHLY
    from datetime import datetime
    expected = rrule(
        MONTHLY, 
        dtstart = PAYMENT_START,
        interval = 1,
    ).after(datetime.now()) 

    for a in ['day', 'month', 'year']:
        assert getattr(expected, a) == getattr(new_payment.active_on, a)
        
    assert expected.day == PAYMENT_START.day 
        
    
    
# POST parameters used often
signup_params_no_cc = dict(
    first_name = 'billy',
    last_name = 'bob',
    email = 'billybob@lala.net',
    username = 'billybob',
    password = 'password',
    password2 = 'password',
    group = 'billybob carpet cleaning',
    timezone = settings.ACCOUNT_TIME_ZONES[0][0],
    subdomain = 'billybob',
    domain = settings.ACCOUNT_DOMAINS[1][0],
    terms_of_service = True,
)
cc_params = dict(
    card_type = 0,
    card_number = '411111111111',
    card_expiration = date.today()
    
)
change_payment_method_params = dict(
    first_name = 'billy',
    last_name = 'bob',                    
    card_number = '411111111111',
    card_expiration = date.today()    
)
        

class SubscriptionTests(IntegrationTest):
    fixtures = [
        'test/accounts.json', 
        'test/people.json', 
        'test/groups.json', 
        'test/roles.json',
    ]
    def setUp(self):
        recurring_payment.gateway = MockGateway()
        recurring_payment.gateway.reset()
        
    
    ############################
    # Signup Tests
    ############################
    
    def test_signup(self):
                #-------------------------------------------------
        # If ssl is not on for GET, redirect to ssl page
        #-------------------------------------------------
        self.assertState(
            'GET',
            CREATE_PATH % 1,
            [
                causes.no_domain,
                causes.no_parameters,
            ],
            [
                effects.redirected(CREATE_PATH % 1, status = 301, ssl = True)
            ]
        )
        #-------------------------------------------------
        # If ssl is not on for POST, 403 Forbidden
        #-------------------------------------------------
        self.assertState(
            'POST',
            CREATE_PATH % 1,
            [
                causes.no_domain,
                causes.no_parameters,
            ],
            [
                effects.status(403)
            ]
        )        
        
        #-------------------------------------------------
        # You can't sign up from a domain belonging
        # to an account.
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            CREATE_PATH % 0,
            [
                causes.ssl,
                causes.person_not_logged_in,
                causes.valid_domain,
            ],
            [
                effects.status(404),
            ]
        )
        
        #-------------------------------------------------
        # Show the signup form
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            CREATE_PATH % 0,
            [
                causes.ssl,
                causes.no_domain,
                causes.no_parameters,
            ],
            [
                effects.rendered('account/signup_form.html'),
                effects.status(200)
            ]
        )
        
        #-------------------------------------------------
        # If the subscription level is invaid, show 404
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            CREATE_PATH % 789, # 789 is invalid subscription level
            [
                causes.ssl,
                causes.no_domain,
                causes.no_parameters,
            ],
            [
                effects.status(404)
            ]
        )
        
            
        #-------------------------------------------------
        # If the subscription level is free, a credit
        # card is not required.
        #-------------------------------------------------
        self.assertState(
            'POST',
            CREATE_PATH % 0, # 0 is Free Account
            [
                causes.ssl,
                delete_test_account,
                causes.no_domain,
                causes.params(**signup_params_no_cc),
            ],
            [
                effects.redirected_to_url(
                    "http://%s/" % domain
                ),
                effects.exists(
                    Account, 
                    subdomain = signup_params_no_cc['subdomain'],
                    domain = signup_params_no_cc['domain'],
                ),
                effects.exists(Person, email = 'billybob@lala.net'),
                effects.person_has_role('account_admin', username = 'billybob'),
            ]
        )
        
        #-------------------------------------------------
        # If the subscription level is NOT free, a credit
        # card IS required.
        #-------------------------------------------------
        self.assertState(
            'POST',
            CREATE_PATH % 1, # 1 is Silver (pay) account
            [
                causes.ssl,
                delete_test_account,
                causes.no_domain,
                causes.params(**signup_params_no_cc),
            ],
            [
                effects.rendered('account/signup_form.html'),
                effects.does_not_exist(Person, email = 'billybob@lala.net'),
                effects.does_not_exist(
                    Account, 
                    subdomain = signup_params_no_cc['subdomain'],
                    domain = signup_params_no_cc['domain'],
                ),
                effects.status(200)
            ]
        )
        
        #-------------------------------------------------
        # If everything validates, create a person, account
        # and recurring payment.
        #-------------------------------------------------
        self.assertState(
            'POST',
            CREATE_PATH % 1, # 1 is Silver (pay) account
            [
                causes.ssl,
                delete_test_account,
                causes.no_domain,
                causes.params(**signup_params_no_cc),
                causes.params(**cc_params),
            ],
            [
                effects.redirected_to_url(
                    "http://%s/" % domain
                ),
                effects.exists(
                    Account, 
                    subdomain = signup_params_no_cc['subdomain'],
                    domain = signup_params_no_cc['domain'],
                ),
                effects.exists(Person, email = 'billybob@lala.net'),
                effects.person_has_role('account_admin', username = 'billybob'),
                effects.exists(RecurringPayment, name = 'billy bob'),
            ]
        )
        
        
        #-------------------------------------------------
        # If the gateway returns an unrecognized response,
        # show a special message & email the administrator.
        #-------------------------------------------------
        self.assertState(
            'POST',
            CREATE_PATH % 1, # 1 is Silver (pay) account
            [
                causes.ssl,
                delete_test_account,
                causes.no_domain,
                causes.params(**signup_params_no_cc),
                causes.params(**cc_params),
                payment_response_error
            ],
            [
                effects.outbox_len(1),
                effects.rendered('account/payment_create_error.html'),
            ]
        )
        
        #-------------------------------------------------
        # If the gateway does not accept the payment info,
        # show the form.
        #-------------------------------------------------
        self.assertState(
            'POST',
            CREATE_PATH % 1, # 1 is Silver (pay) account
            [
                causes.ssl,
                delete_test_account,
                causes.no_domain,
                causes.params(**signup_params_no_cc),
                causes.params(**cc_params),
                payment_request_error,
            ],
            [
                effects.rendered('account/signup_form.html'),
                effects.status(200)
            ]
        )
        
        
        
    ############################
    # Change Payment Method Tests
    ############################
        
    def test_change_payment_method(self):
        security.check_account_inactive_ok(self, CHANGE_PM_PATH, causes.ssl)
        security.require_ssl(self, CHANGE_PM_PATH)
            
        #-------------------------------------------------
        # The form is shown
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            CHANGE_PM_PATH,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                causes.no_parameters,
            ],
            [
                effects.rendered('account/payment_method_form.html'),
                effects.status(200)
            ]
        )
        
            
        #-------------------------------------------------
        # The form is shown if input is invalid
        #-------------------------------------------------
        self.assertState(
            'POST',
            CHANGE_PM_PATH,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                causes.no_parameters,
                causes.params(
                    first_name = 'billy',
                    last_name = 'bob',                    
                    card_number = '411111111111',
                    card_expiration = None
                )
            ],
            [
                effects.rendered('account/payment_method_form.html'),
                effects.status(200)
            ]
        )
        
        #-------------------------------------------------
        # If input is valid, a RecurringPayment is created
        #-------------------------------------------------
        self.assertState(
            'POST',
            CHANGE_PM_PATH,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                causes.no_parameters,
                causes.params(
                    first_name = 'billy',
                    last_name = 'bob',                    
                    card_number = '411111111111',
                    card_expiration = date.today()
                ),
                account_has_no_payment_method,
            ],
            [
                effects.exists(
                    RecurringPayment, 
                    account__subdomain = 'starr'
                ),
                effects.rendered('account/payment_method_form.html'),
                effects.status(200)
            ]
        )
        
            
        #-------------------------------------------------
        # If input is valid, and a RecurringPayment exists,
        # the old RecurringPayment is deleted and a new one
        # is created.
        #-------------------------------------------------
        self.assertState(
            'POST',
            CHANGE_PM_PATH,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                causes.no_parameters,
                causes.params(**change_payment_method_params),
                account_has_payment_method,
            ],
            [
                gateway_cancel_called,
                new_payment_starts_when_old_one_stops,
                effects.exists(RecurringPayment, account__pk = 1),
                effects.rendered('account/payment_method_form.html'),
                effects.status(200)
            ]
        )
        
        #-------------------------------------------------
        # If we get a PeymentRequestError, it means that
        # the user probably entered some invalid info.
        # If the payment gateway returned this error, a 
        # RecurringPayment is NOT created.
        #-------------------------------------------------
        
        self.assertState(
            'POST',
            CHANGE_PM_PATH,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                causes.no_parameters,
                causes.params(**change_payment_method_params),
                account_has_no_payment_method,
                payment_request_error,
            
            ],
            [
                gateway_cancel_called,
                effects.does_not_exist(
                    RecurringPayment, 
                    account__pk = 1,
                ),
                effects.does_not_exist(
                    RecurringPayment, 
                    name = 'billy bob'
                ),
                effects.rendered('account/payment_method_form.html'),
                effects.status(200)
            ]
        )
        
        #-------------------------------------------------
        # If we get a PeymentRequestError, it means that
        # the user probably entered some invalid info.
        # If the payment gateway returned this error, AND a
        # RecurringPayment exists for the account, do NOT
        # delete it.
        #-------------------------------------------------
        self.assertState(
            'POST',
            CHANGE_PM_PATH,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                causes.no_parameters,
                causes.params(**change_payment_method_params),
                account_has_payment_method,
                payment_request_error,
            
            ],
            [
                gateway_cancel_called,
                effects.exists(
                    RecurringPayment, 
                    account__pk = 1,
                ),
                effects.count(1, RecurringPayment, name = 'Bob Jones'),
                effects.count(0, RecurringPayment, name = 'billy bob'),
                effects.rendered('account/payment_method_form.html'),
                effects.status(200)
            ]
        )
        
        #-------------------------------------------------
        # If there is a PaymentResponse error, it means
        # we couldn't understand the response from the 
        # gateway. So a special error page is displayed
        # and the administrator is emailed.
        #-------------------------------------------------
        
        self.assertState(
            'POST',
            CHANGE_PM_PATH,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                causes.no_parameters,
                causes.params(**change_payment_method_params),
                account_has_payment_method,
                payment_response_error,
            
            ],
            [
                gateway_cancel_called,
                effects.exists(
                    RecurringPayment, 
                    account__pk = 1,
                ),
                effects.outbox_len(1),
                effects.count(1, RecurringPayment, name = 'Bob Jones'),
                effects.count(0, RecurringPayment, name = 'billy bob'),
                effects.rendered('account/payment_create_error.html'),
                effects.status(200)
            ]
        )
        
        #-------------------------------------------------
        # If there is a PaymentResponse error when canceling
        # an existing payment, it is very bad. It means that 
        # the customer will be billed twice! So we diaplay a
        # special error message, and email the administrator.
        #-------------------------------------------------
        self.assertState(
            'POST',
            CHANGE_PM_PATH,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                causes.no_parameters,
                causes.params(**change_payment_method_params),
                account_has_payment_method,
                payment_response_error_on_cancel,
            
            ],
            [
                gateway_cancel_called,
                effects.exists(
                    RecurringPayment, 
                    account__pk = 1,
                ),
                effects.outbox_len(1),
                effects.count(0, RecurringPayment, name = 'Bob Jones'),
                effects.count(1, RecurringPayment, name = 'billy bob'),
                effects.rendered('account/payment_cancel_error.html'),
                effects.status(200)
            ]
        )
        
        
    ############################
    # Cancel Payment Method Tests
    ############################
        
    def test_cancel_payment_method(self):
        security.check(self, CANCEL_PM_PATH)
        
        #-------------------------------------------------
        # If the account does NOT have a RecurringPayment, 
        # then the account is deactivated immediately.
        #-------------------------------------------------
        self.assertState(
            'POST',
            CANCEL_PM_PATH,
            [
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_no_payment_method,
            ],
            [
                effects.field_value(Account, {'pk': 1}, active = False),
                effects.redirected('/account/reactivate_free_account/')
            ]
        )
        
        #-------------------------------------------------
        # If the account has a RecurringPayment, show the form
        #-------------------------------------------------
        self.assertState(
            'GET',
            CANCEL_PM_PATH,
            [
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_payment_method,
            ],
            [
                effects.field_value(Account, {'pk': 1}, active = True),
                effects.rendered('account/payment_cancel_form.html'),
                effects.status(200)
            ]
        )
        
        #-------------------------------------------------
        # If the account does not have a RecurringPayment, show the form
        #-------------------------------------------------
        self.assertState(
            'GET',
            CANCEL_PM_PATH,
            [
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_no_payment_method,
            ],
            [
                effects.field_value(Account, {'pk': 1}, active = True),
                effects.rendered('account/payment_cancel_form.html'),
                effects.status(200)
            ]
        )
            
        #-------------------------------------------------
        # If the form is posted, and a payment exists, the
        # payment is canceled. Note that it is not deleted.
        # Instead, the inactive flag is set, which triggers
        # the account for suspension whenever payment runs
        # out. 
        #-------------------------------------------------
        self.assertState(
            'POST',
            CANCEL_PM_PATH,
            [
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_payment_method,
            ],
            [
                effects.field_value(Account, {'pk': 1}, active = True),
                effects.redirected('/account/'),
                effects.count(1, RecurringPayment, account__pk = 1),
                payment_is_inactive,
                
            ]
        )
        
        #-------------------------------------------------
        # If a gateway error is returned on cancel, show
        # the error page and email admin
        #-------------------------------------------------
        self.assertState(
            'POST',
            CANCEL_PM_PATH,
            [
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_payment_method,
                payment_response_error_on_cancel,
            ],
            [
                effects.field_value(Account, {'pk': 1}, active = True),
                effects.outbox_len(1),
                effects.rendered('account/payment_cancel_error.html'),
                effects.count(1, RecurringPayment, account__pk = 1),
                payment_is_active,
                
            ]
        )
        
        
        
    ############################
    # Upgrade Tests
    ############################
    
    def test_upgrade(self):

        security.check(self, UPGRADE_PATH % 2, causes.ssl)
        security.require_ssl(self, UPGRADE_PATH % 2)
            
        #-------------------------------------------------
        # Show Form
        #-------------------------------------------------
        self.assertState(
            'GET',
            UPGRADE_PATH % 2,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_payment_method,
            ],
            [
                effects.rendered('account/upgrade_form.html')
            ]
        )
        
        #-------------------------------------------------
        # If invalid subscription level, 404 - Not Found
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            UPGRADE_PATH % 666,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_payment_method,
            ],
            [
                effects.status(404)
            ]
        )
        #-------------------------------------------------
        # If account alreay has subscription label, 403 - Forbidden
        #-------------------------------------------------
        self.assertState(
            'POST',
            UPGRADE_PATH % 1,
            [
                causes.ssl,
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_payment_method,
            ],
            [
                effects.status(403)
            ]
        )
        #-------------------------------------------------
        # If everything is valid, and the account has a
        # RecurringPayment, change level and change payment
        #-------------------------------------------------
        self.assertState(
            'POST',
            UPGRADE_PATH % 2,
            [
                causes.ssl,
                account_has_subscription_level(1),
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_payment_method,
            ],
            [
                gateway_change_called,
                effects.redirected('/account/'),
                subscription_level_is(2)
            ]
        )
        #-------------------------------------------------
        # If the account has an inactive RecurringPayment, 
        # new CC info is required
        #-------------------------------------------------
        self.assertState(
            'POST',
            UPGRADE_PATH % 2,
            [
                causes.ssl,
                account_has_subscription_level(1),
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_inactive_payment_method,
                causes.params(**change_payment_method_params)
            ],
            [
                gateway_change_called,
                effects.redirected('/account/'),
                subscription_level_is(2)
            ]
        )
        #-------------------------------------------------
        # If the account does not have a RecurringPayment, 
        # credit card params are required. 
        #-------------------------------------------------
        self.assertState(
            'POST',
            UPGRADE_PATH % 2,
            [
                causes.ssl,
                account_has_subscription_level(1),
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_no_payment_method,
            ],
            [
                effects.rendered('account/upgrade_form.html'),
                subscription_level_is(1)
            ]
        )
        #-------------------------------------------------
        # If the account doesn't have a RecurringPayment, 
        # and you've provided billing information, change
        # subscription level.
        #-------------------------------------------------
        self.assertState(
            'POST',
            UPGRADE_PATH % 2,
            [
                causes.ssl,
                account_has_subscription_level(1),
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_no_payment_method,
                causes.params(**change_payment_method_params)
            ],
            [
                gateway_start_called,
                effects.redirected('/account/'),
                subscription_level_is(2)
                
            ]
        )
        
        #-------------------------------------------------
        # If the gateway returns an unrecognized response,
        # show a special message & email the administrator.
        #-------------------------------------------------
        self.assertState(
            'POST',
            UPGRADE_PATH % 2, 
            [
                causes.ssl,
                account_has_subscription_level(1),
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_no_payment_method,
                causes.params(**change_payment_method_params),
                payment_response_error,
            ],
            [
                effects.outbox_len(1),
                effects.rendered('account/payment_create_error.html'),
                subscription_level_is(1)
            ]
        )
        
        #-------------------------------------------------
        # If the gateway does not accept the payment info,
        # show the form.
        #-------------------------------------------------
        self.assertState(
            'POST',
            UPGRADE_PATH % 2,
            [
                causes.ssl,
                account_has_subscription_level(1),
                causes.valid_domain,
                causes.owner_logged_in,
                account_has_no_payment_method,
                causes.params(**change_payment_method_params),
                payment_request_error,
            ],
            [
                effects.rendered('account/upgrade_form.html'),
                effects.status(200)
            ]
        )
        
        
        
        
        
        
        
    ############################
    # Edit account Tests
    ############################
        
    def test_edit_account(self):
        security.check(self, EDIT_ACCOUNT_PATH)
        
        #-------------------------------------------------
        # Show the form when no params
        #-------------------------------------------------
        self.assertState(
            'GET/POST',
            EDIT_ACCOUNT_PATH,
            [
                causes.valid_domain,
                causes.owner_logged_in,
                causes.no_parameters,
            ],
            [
                effects.status(200),
                effects.rendered('account/account_form.html'),
            ]
        )
        
        #-------------------------------------------------
        # Show the form when invalid params
        #-------------------------------------------------
        self.assertState(
            'POST',
            EDIT_ACCOUNT_PATH,
            [
                causes.valid_domain,
                causes.owner_logged_in,
                causes.params(
                    domain = '---',
                ),
            ],
            [
                effects.status(200),
                effects.rendered('account/account_form.html'),
            ]
        )
        #-------------------------------------------------
        # If everything's valid, changes are saved
        # The user is redirected to the subdomain.domain
        #-------------------------------------------------
        edit_account_params = dict(
            subdomain = 'newname',
            domain = settings.ACCOUNT_DOMAINS[1][0],
            name = 'newname',
            timezone = settings.ACCOUNT_TIME_ZONES[1][0],
        )
        self.assertState(
            'POST',
            EDIT_ACCOUNT_PATH,
            [
                causes.valid_domain,
                causes.owner_logged_in,
                causes.params(**edit_account_params),
            ],
            [
                effects.field_value(
                    Account, 
                    {'pk': 1}, 
                    **edit_account_params
                ),
                effects.redirected_to_url(
                    'http://%s.%s/account/' % (
                        edit_account_params['subdomain'], 
                        settings.ACCOUNT_DOMAINS[1][0])),
            ]
        )
        
        
        
        
