from django.http import HttpResponse, Http404, HttpResponseForbidden, HttpResponsePermanentRedirect, get_host, HttpResponseRedirect
from models import Account, Person
from django.core.exceptions import ObjectDoesNotExist
import views.authentication
import views.subscription
from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.sessions.middleware import SessionWrapper
from django.utils.cache import patch_vary_headers
import datetime        
import helpers
        
def add_account_to_context(request):
    data = {}
    try:
        data['account'] = request.account
    except AttributeError:
        pass
    
    try:
        data['person'] = request.person
    except AttributeError:
        pass
    
    return data
    
    
class AccountBasedAuthentication(object):
    """
    Loads current account and person into request.
    Allows or denies access to urls based on login
    state and person roles.
    """
    def process_request(self, request):
        Account.load_from_request(request)
        Person.load_from_request(request)
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        This function uses the contents of view_kwargs['meta'] 
        determine access rights.
        
        The rules are:
        
        meta['requires_account'] == False: 
            show view only if account is not present
        
        meta['requires_login'] == True: 
            show view only if person is logged in
        
        meta['requires_logout'] == True: 
            show view only if person is not logged in 
        
        meta['requires_resource'] == 'widget': 
            show view only if account has 'widget' resources.
            Redirects to upgrade screen if not.
            
        meta['roles'] == 'role1 & (role2 | role 3)':
            Show view if person is logged in &
            has role1 and either role2 or role3
        
        meta['roles'] == None or '' or <not set>
            Show view without checking roles.
        """
        
        
        if 'meta' not in view_kwargs:
            return None
        
        meta = view_kwargs.pop('meta')
        
        # SSL 
        if meta.get('ssl') and not request.is_secure():
            if request.method == 'GET':
                return self._redirect(request, True)
            else:
                return HttpResponseForbidden()
        
        # Requires account
        account = getattr(request, 'account', None)
        
        if meta.get('requires_account', True):
            if not account:
                raise Http404
        else:
            if account:
                raise Http404
            else:
                return None
            
        # Requires account to be active
        if not account.active:
            if not meta.get('inactive_account_ok'):
                return HttpResponseRedirect('/account/inactive/')
            
        
        # Requires login
        if 'roles' in meta:
            meta['requires_login'] = True
            
        person = getattr(request, 'person', None)
        
        if meta.get('requires_logout') and person:
            return HttpResponseForbidden()
        
        if meta.get('requires_login') and not person:
            return helpers.redirect(
                views.authentication.login
            )
        
        # Requires reource
        if not account.has_resource(meta.get('requires_resource')):
            return helpers.redirect(
                views.subscription.upgrade
            )
        
        if not person:
            return None
                
        # Requires role
        if person.has_roles(meta.get('roles')):
            return None
        else:
            return HttpResponseForbidden()
            

    def _redirect(self, request, secure):
        protocol = secure and "https" or "http"
        newurl = "%s://%s%s" % (protocol,get_host(request),request.get_full_path())
        if settings.DEBUG and request.method == 'POST':
            raise RuntimeError, \
        """Django can't perform a SSL redirect while maintaining POST data.
           Please structure your views so that redirects only occur during GETs."""

        return HttpResponsePermanentRedirect(newurl)       
    
    
        
class DualSessionMiddleware(object):
    """Session middleware that allows you to turn individual browser-length 
    sessions into persistent sessions and vice versa.
    
    This middleware can be used to implement the common "Remember Me" feature
    that allows individual users to decide when their session data is discarded.
    If a user ticks the "Remember Me" check-box on your login form create
    a persistent session, if they don't then create a browser-length session.
    
    This middleware replaces SessionMiddleware, to enable this middleware:
    - Add this middleware to the MIDDLEWARE_CLASSES setting in settings.py, 
      replacing the SessionMiddleware entry.
    - In settings.py add this setting: 
      PERSISTENT_SESSION_KEY = 'sessionpersistent'
    - Tweak any other regular SessionMiddleware settings (see the sessions doc),
      the only session setting that's ignored by this middleware is 
      SESSION_EXPIRE_AT_BROWSER_CLOSE. 
      
    Once this middleware is enabled all sessions will be browser-length by
    default.
    
    To make an individual session persistent simply do this:
    
    session[settings.PERSISTENT_SESSION_KEY] = True
    
    To make a persistent session browser-length again simply do this:
    
    session[settings.PERSISTENT_SESSION_KEY] = False
    
    CREDIT: http://code.djangoproject.com/wiki/CookBookDualSessionMiddleware
    """
    
    def process_request(self, request):
        request.session = SessionWrapper(request.COOKIES.get(settings.SESSION_COOKIE_NAME, None))

    def process_response(self, request, response):
        # If request.session was modified, or if response.session was set, save
        # those changes and set a session cookie.
        patch_vary_headers(response, ('Cookie',))
        try:
            modified = request.session.modified
        except AttributeError:
            pass
        else:
            if modified or settings.SESSION_SAVE_EVERY_REQUEST:
                session_key = request.session.session_key or Session.objects.get_new_session_key()
                if not request.session.get(settings.PERSISTENT_SESSION_KEY, False):
                    # session will expire when the user closes the browser
                    max_age = None
                    expires = None
                else:
                    
                    max_age = settings.SESSION_COOKIE_AGE
                    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.SESSION_COOKIE_AGE), "%a, %d-%b-%Y %H:%M:%S GMT")
                
                new_session = Session.objects.save(session_key, 
                                                   request.session._session,
                                                   datetime.datetime.now() + datetime.timedelta(seconds=settings.SESSION_COOKIE_AGE))
                response.set_cookie(settings.SESSION_COOKIE_NAME, session_key,
                                    max_age = max_age, expires = expires, 
                                    domain = settings.SESSION_COOKIE_DOMAIN,
                                    secure = settings.SESSION_COOKIE_SECURE or None)
        return response        
        
        
        
        
        
        
        
        