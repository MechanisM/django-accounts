from django.http import HttpResponse, HttpResponseRedirect
from operator import eq
from urlparse import urlparse
from django.core import mail
from account.models import Person, Account

class Void: pass

def breakpoint(client, response, testcase):
    import pdb
    pdb.set_trace()
    
    
#def logged_in(client, response, testcase):
    #""" Check that the default person is logged in """
    #person = Person.objects.get(username = 'snhorne')
    
    ## client.previous_request is only available
    ## in patched test client.
    #if hasattr(client, 'previous_request'):
        #testcase.assertEqual(
            #client.previous_request.person,
            #person
        #)
    #testcase.assertEqual(
        #client.session[Person.SESSION_KEY],
        #person.id,
    #)
        
def person_logged_in(**criteria):
    def logged_in(client, response, testcase):
        """ Check that the default person is logged in """
        person = Person.objects.get(**criteria)
        
        # client.previous_request is only available
        # in patched test client.
        if hasattr(client, 'previous_request'):
            testcase.assertEqual(
                client.previous_request.person,
                person
            )
        testcase.assertEqual(
            client.session[Person.SESSION_KEY],
            person.id,
        )
    return logged_in
        
    
logged_in = person_logged_in(pk = 1)
    
def not_logged_in(client, response, testcase):
    """ Check that noone is logged in """
    # client.previous_request is only available
    # in patched test client.
    if hasattr(client, 'previous_request'):
        testcase.assertEqual(
            getattr(client.previous_request, 'person', None),
            None
        )
    
def status(code):
    """ Check the HTTP response status code """
    def has_status(client, response, testcase):
        testcase.assertEqual(
            response.status_code,
            code
        )
    return has_status
    
def rendered(template):
    """ Check that the template was rendered """
    def was_rendered(client, response, testcase):
        testcase.assertTemplateUsed(response, template)
    return was_rendered

def redirected(path, status=302, ssl=False):
    """ 
    Check that user was redirected to path 
    `status`: the status code expected.
    'ssl': set to true if you expect to redirect to https from http
    """
    def was_redirected(client, response, testcase):
        if ssl:
            client.defaults['HTTPS'] = 'on'
        testcase.assertRedirects(response, path, status_code=status)
    return was_redirected


def redirected_to_url(url):
    """ Checks for redirection to a whole url, not just a path """
    def was_redirected(client, response, testcase):
        status(302)(client, response, testcase)
        testcase.assertEqual(
            response['Location'],
            url
        )
    return was_redirected
    
    
def context(key, value = Void, type = Void):
    """ Check that a key exists in context w/ matching value """
    def is_in_context(client, response, testcase):
        # If multiple templates are called, context
        # is actually a list of contexts, so we check
        # the value in all of them.
        if isinstance(response.context, list):
            contexts = response.context
        else:
            contexts = [response.context]
            
        for context in contexts:
            assert key in context
            if value is not Void:
                testcase.assertEqual(
                    value, 
                    context[key]
                )
            if type is not Void:
                testcase.assertTrue(
                    isinstance(
                        context[key], 
                        type
                    )
                )
    return is_in_context

def form_errors(name):
    def has_errors(client, response, testcase):
        if isinstance(response.context, list):
            contexts = response.context
        else:
            contexts = [response.context]
        for context in contexts:
            assert context[name]._errors
            
    return has_errors

    
    
    
def outbox_len(count):
    """ Check that the email.outbox contains n items """
    def outbox_len_is(client, response, testcase):
        testcase.assertEqual(
            len(mail.outbox),
            count
        )
    return outbox_len_is
        

def logged_in_has_password(password):
    """ Check that a password matches that of the logged in user """
    def check_password(client, response, testcase):
        # client.previous_request is only available
        # in patched test client.
        if hasattr(client, 'previous_request'):
            assert client.previous_request.person.check_password(password)
    return check_password
    
def person_has_password(pk, password):
    def check_password(client, response, testcase):
        assert Person.objects.get(pk = pk).check_password(password)
    return check_password
        
def person_has_role(role, **criteria):
    def check_role(client, response, testcase):
        assert Person.objects.get(**criteria).has_roles(role)
    return check_role

def person_does_not_have_role(role, **criteria):
    def check_role(client, response, testcase):
        assert not Person.objects.get(**criteria).has_roles(role)
    return check_role

def session_expires_on_close(client, response, testcase):
    testcase.assertEqual(
        response.cookies['sessionid']['max-age'],
        ''
    )
    
def session_persists_after_close(client, response, testcase):
    testcase.assertTrue(
        int(response.cookies['sessionid']['max-age'] or '0') > 0
    )
    
def created(ModelClass):
    def check_created(client, response, testcase):
        old_count = client.alters[ModelClass]
        testcase.assertEqual(
            ModelClass.objects.count(),
            old_count + 1
        )
    return check_created
    
def does_not_exist(ModelClass, **kwargs):
    def check_exist(client, response, testcase):
        try:
            ModelClass.objects.get(**kwargs)
            raise False
        except ModelClass.DoesNotExist:
            pass
    return check_exist
    
def exists(ModelClass, **kwargs):
    def check_exist(client, response, testcase):
        ModelClass.objects.get(**kwargs)
    return check_exist



def count(n, ModelClass, **kwargs):
    def check_count(client, response, testcase):
        assert ModelClass.objects.filter(**kwargs).count() == n
    return check_count



def field_value(ModelClass, criteria, **kwargs):
    def check_eq(client, response, testcase):
        obj = ModelClass.objects.get(**criteria)
        for key in kwargs:
            assert getattr(obj, key) == kwargs[key]
        
    return check_eq

def apply(ModelClass, criteria, method, params, expected=True):
    def check_fn(client, response, testcase):
        obj = ModelClass.objects.get(**criteria)
        assert getattr(obj, method, **params) == expected
        
    return check_fn








