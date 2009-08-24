import logging
from django.http import HttpResponseServerError, Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template import loader, Context
from django.contrib.auth import authenticate, logout
from person_forms import LoginForm, ResetPasswordForm
from django.conf import settings
import generic
from ..models import Person
from .. import helpers
    

def requires_post(fn):
    def require_post_wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            return fn(request, *args, **kwargs)
        else:
            return helpers.requires_post()
    return require_post_wrapper

def require_auth(fn):
    """ Allow the action method only for authenticated user
    """
    def require_account_wrapper(request, *args, **kwargs):
        if request.person:
            return fn(request, *args, **kwargs)
        else:
            raise Http404
    return require_account_wrapper
        
def require_roles(roles_string):
    """ Roles required decoration. user must exist before
    """
    def _dec(view_func):
        def _checklogin(request, *args, **kwargs):
            if request.person and request.person.has_roles(roles_string):
                return view_func(request, *args, **kwargs)
            return HttpResponseRedirect('%s?%s=%s' % ('/person/login', REDIRECT_FIELD_NAME, quote(request.get_full_path())))
        return _checklogin
    return _dec


def login(request):
    if request.method == "POST":    
        loginform = LoginForm(request.POST)
        if loginform.login(request):            
            if request.account.active:
                return HttpResponseRedirect('/')
            elif request.person.has_roles('account_admin'):
                import subscription
                if request.account.subscription_level['price']:
                    return helpers.redirect(subscription.change_payment_method)
                else:
                    return helpers.redirect(subscription.reactivate_free_account)
            else:
                return HttpResponseRedirect('/account/inactive/')
                
    else:
        loginform = LoginForm()
        
    return helpers.render(
        request,
        'account/login_form.html', 
        {
            'form': loginform, 
        }
    )
    
@requires_post
def logout(request):
    Person.logout(request)
    return helpers.redirect(login)


def reset_password(request):
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        person = form.get_person(request)
        if person:
            new_password = person.reset_password()
            t = loader.get_template('account/reset_password_email.txt')
            c = Context({
                'person': person,
                'account': request.account,
                'new_password': new_password,
            })
            person.send_email(
                "Your password has been reset.", 
                t.render(c),
            )
            person.save()
            logging.debug("Reset password for user #%i to '%s'" % (person.id, new_password))
            
            return helpers.render(
                request,
                'account/reset_password_success.html', 
                {'account': request.account},
            )
    else:
        form = ResetPasswordForm()
        
    return helpers.render(
        request,
        'account/reset_password_form.html',
        {'form': form}
    )
    

def edit_self(request, **kwargs):
    return generic.edit(
        request, 
        id = request.person.id, 
        model = Person,
        **kwargs
    )
    








