from django.test.client import Client
from account.models import Person, Account

def _remove(collection, key):
    try:
        del collection[key]
    except KeyError:
        pass
    
def breakpoint(client, parameters):
    import pdb; pdb.set_trace()
    return client, parameters
               
def ssl(client, parameters):
    client.defaults['HTTPS'] = 'on'
    return client, parameters

               
               
def person_logged_in(client, parameters):
    """ Logs in the default person. """
    client.post(
        '/person/login/', 
        {
            'username': 'snhorne', 
            'password': 'password',
        },
        HTTP_HOST = 'starr.localhost',
        HTTPS = 'on',
    )
    return client, parameters

def owner_logged_in(client, parameters):
    """ Logs in the default person. """
    client.post(
        '/person/login/', 
        {
            'username': 'kmnicholson', 
            'password': 'password',
        },
        HTTP_HOST = 'starr.localhost',
        HTTPS = 'on',
    )
    return client, parameters

def person_not_logged_in(client, parameters):
    """ Clears any logged in people """
    _remove(client.session, Person.SESSION_KEY)
    return client, parameters

def valid_domain(client, parameters):
    """ Sets a valid domain """
    client.defaults['HTTP_HOST'] = 'starr.localhost'
    return client, parameters

def account_inactive(client, parameters):
    account = Account.objects.get(pk=1)
    account.active = False
    account.save()
    return client, parameters

def account_active(client, parameters):
    """ Sets a valid domain """
    account = Account.objects.get(pk=1)
    account.active = True
    account.save()
    return client, parameters

def mismatched_domain(client, parameters):
    """ Sets a domain that is valid but doesn't 
    include the default user """
    client.defaults['HTTP_HOST'] = 'kristi.localhost'
    return client, parameters

def invalid_domain(client, parameters):
    """ Sets an invalid domain """
    client.defaults['HTTP_HOST'] = 'invalid'
    return client, parameters

def no_domain(client, parameters):
    """ Clears any domain """
    _remove(client.defaults, 'HTTP_HOST')
    return client, parameters

def no_parameters(client, parameters):
    """ Clears params """
    return client, {}

def valid_username(client, parameters):
    """ Sets a valid username """
    parameters['username'] = 'snhorne'
    return client, parameters
    
def invalid_username(client, parameters):
    """ Sets an invalid username """
    parameters['username'] = '1leethax0r'
    return client, parameters
    
def valid_login_parameters(client, parameters):
    """ Sets login params for default user """
    parameters.update({
        'username': 'snhorne',
        'password': 'password',
    })
    return client, parameters

def valid_admin_login_parameters(client, parameters):
    """ Sets login params for admin user """
    parameters.update({
        'username': 'kmnicholson',
        'password': 'password',
    })
    return client, parameters

def invalid_login_parameters(client, parameters):
    """ Sets Invalid Login Params """
    parameters.update({
        'username': 'snhorne',
        'password': 'not a real password',
    })
    return client, parameters

def no_login_parameters(client, parameters):
    """ Clears Login Params """
    _remove(parameters, 'username')
    _remove(parameters, 'password')
    return client, parameters

def remember_me_not_checked(client, parameters):
    """ Sets 'remember me' option of login form to false """
    parameters['remember_me'] = ''
    return client, parameters
    
def remember_me_checked(client, parameters):
    """ Sets 'remember me' option of login form to True """
    parameters['remember_me'] = 'on'
    return client, parameters

def invalid_create_person_parameters(client, parameters):
    parameters.update({
        'email': 'x',
    })
    return client, parameters

def valid_create_person_parameters(client, parameters):
    parameters.update({
        'username': 'bob_jones',
        'password': 'password',
        'first_name': 'bob',
        'last_name': 'jones',
        'email': 'bob@email.com',
    })
    return client, parameters



def alters(ModelClass):
    def set_alters(client, parameters):
        client.__dict__.setdefault(
            'alters',
            {}
        )[ModelClass] = ModelClass.objects.count()
        return client, parameters
    return set_alters

    
def params(**kwargs):
    def set_params(client, parameters):
        parameters.update(kwargs)
        return client, parameters
    return set_params

    
