from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseServerError, HttpResponseForbidden
import django.newforms as forms
from django.conf import settings
from django.shortcuts import render_to_response
from person_forms import SignupForm, PaymentForm, UpgradeForm, AccountForm
from .. import helpers
from ..models import Account, Person, RecurringPayment
from account.lib.payment.errors import PaymentRequestError, PaymentResponseError
from django.core import mail


def _email_cancel_error_to_admin(account, old_payment, new_payment=None):
    mail.mail_admins(
        "! Payment Cancel Error", 
        """
        There was an error canceling payment for %s.
        Account Id: %i
        Old Payment Gateway Token: %s
        New Payment Gateway Token: %s
        
        This should NOT ever happen unless there is a problem with
        the gateway interface on your end, or the payment gateway 
        changed their API.
        """ % (
            account.name,
            account.id,
            old_payment.gateway_token,
            getattr(new_payment, 'gateway_token', '(no new payment)')
            ),
        fail_silently = settings.EMAIL_FAIL_SILENTLY,
    )
    
def _email_create_error_to_admin(account=None):
    mail.mail_admins(
        "! Payment Create Error", 
        """
        There was an error canceling payment for %s.
        Account Id: %s
        
        This should NOT ever happen unless there is a problem with
        the gateway interface on your end, or the payment gateway 
        changed their API.
        """ % (
            getattr(account, 'name', '(No account yet)'),
            str(getattr(account, 'id', '(No account yet)')),
            ),
        fail_silently = settings.EMAIL_FAIL_SILENTLY,
    )

    
def edit_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.update_account(request.account)
            return HttpResponseRedirect(
                'http://%s/account/' % request.account.full_domain
            )
            
    else:
        form = AccountForm()
        form.load_from_instance(request.account)
    return helpers.render(
        request,
        'account/account_form.html',
        {
            'form': form,
            'subscription_levels': settings.SUBSCRIPTION_LEVELS,
        }
    )
    
def reactivate_free_account(request):
    if request.method == 'POST':
        if not request.account.subscription_level['price']:
            request.account.active = True
            request.account.save()
        return HttpResponseRedirect('/')
    else:
        return helpers.render(
            request,
            'account/reactivate_free_form.html',
        )
    
def change_payment_method(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            
            old_payment = request.account.recurring_payment
            
            try:
                # Create new recurring transaction:
                new_payment = form.save_payment(
                    request.account,
                    request.account.subscription_level,
                    commit = False,
                    start_date = old_payment and old_payment.next_payment()
                )
                
                # Change the DB records 
                if old_payment: 
                    old_payment.delete()
                    
                new_payment.save()
                request.account.save() # was changed by form.save_payment
                
                # Cancel the old recurring transaction:
                try:
                    if old_payment: 
                        old_payment.cancel()
                except (PaymentResponseError, HttpResponseServerError):
                    _email_cancel_error_to_admin(
                        request.account,
                        old_payment, 
                        new_payment
                    )
                    return helpers.render(
                        request,
                        'account/payment_cancel_error.html',
                        {'recurring_payment': old_payment}
                    )
                
            except PaymentResponseError:
                _email_create_error_to_admin(request.account)
                return helpers.render(
                    request,
                    'account/payment_create_error.html'
                )
            
            except PaymentRequestError:
                pass
            
    else:
        form = PaymentForm()
        
    return helpers.render(
        request, 
        'account/payment_method_form.html', 
        { 
            'form': form, 
            'recurring_payment': request.account.recurring_payment
        }
    )
    
    

def cancel_payment_method(request):
    payment = request.account.recurring_payment
    if request.method == 'POST':
        try:
            if payment:
                # If there is a payment, the account will be
                # deactivated later, at the end of the payment period.
                payment.cancel()
                payment.save()
            else:
                # If there is no payment, that means the user
                # was on a free account. The account is deactivated
                # immediately
                request.account.active = False
                request.account.save()
                return helpers.redirect(reactivate_free_account)
            return helpers.redirect(edit_account)
        except (PaymentResponseError, HttpResponseServerError):
            _email_cancel_error_to_admin(
                request.account,
                payment,
            )
            return helpers.render(
                request,
                'account/payment_cancel_error.html',
                {'recurring_payment': payment}
            )
                
    else:
        return helpers.render(
            request, 
            'account/payment_cancel_form.html', 
            {
                'recurring_payment': payment,
            }
        )
        
    
    
def upgrade(request, level):
    level = int(level)
    try:
        subscription_level = settings.SUBSCRIPTION_LEVELS[level]
    except (IndexError, ValueError):
        raise Http404
    
    # You can't switch to the free plan without canceling the
    # payment. That's more complexity than I want to deal with
    # right now. 
    if not subscription_level['price']:
        return HttpResponseForbidden("Sorry, but you can't switch to the free plan.")
    
    account = request.account
    if account.subscription_level_id == level:
        return HttpResponseForbidden()
    
    payment = request.account.recurring_payment
    
    get_card_info = subscription_level.get('price') and not payment or not payment.is_active()
    
    if request.method == 'POST':
        form = UpgradeForm(
            get_card_info,
            request.POST,
        )
        if form.is_valid():
            try:
                if get_card_info:
                    new_payment = form.save_payment(
                        account, 
                        subscription_level,
                        commit = False
                    )
                    if payment:
                        payment.delete()
                    new_payment.save()
                    account.save()
                    
                else:
                    payment.change_amount(subscription_level['price'])
                    payment.save()
                account.subscription_level_id = level
                account.save()
                return helpers.redirect(edit_account)
            
            except PaymentResponseError:
                # The payment gateway returned an unknown response.
                _email_create_error_to_admin()
                return helpers.render(
                    request,
                    'account/payment_create_error.html'
                )
            
            except PaymentRequestError:
                # The payment gateway rejected our request.
                # Most likely a user input error.
                pass
    else:
        form = UpgradeForm(
            get_card_info
        )
        
    return render_to_response(
        'account/upgrade_form.html', 
        {
            'form': form,
            'subscription_level': subscription_level,
            'requires_payment': get_card_info,
        }
    )

    
    
    
    
def _delete_if_exists(*records):
    for record in records:
        if record and record.id:
            record.delete()
    
    
    
    
    
def create(request, level):
    try:
        subscription_level = settings.SUBSCRIPTION_LEVELS[int(level)]
    except (IndexError, ValueError):
        raise Http404
    
    get_card_info = subscription_level.get('price')
    

    
    if request.method == 'POST':
        form = SignupForm(
            get_card_info,
            request.POST,
        )
        if form.is_valid():
            person, account, payment = None, None, None
            try:
                account = form.save_account(level)
                person = form.save_person(account)
                payment = form.save_payment(account, subscription_level)
                
                person.add_role('account_admin')
            
                return HttpResponseRedirect(
                    'http://%s/' % account.full_domain
                )
            except ValueError:
                # Either person or account could not be created.
                Pass
            except PaymentRequestError:
                # The payment gateway rejected our request.
                # Most likely a user input error.
                pass
            except PaymentResponseError:
                # The payment gateway returned an unknown response.
                _email_create_error_to_admin()
                return helpers.render(
                    request,
                    'account/payment_create_error.html'
                )

            # If everything wasn't created, delete it all. 
            _delete_if_exists(person, account, payment)
                
    else:
        form = SignupForm(
            get_card_info
        )
        
    return render_to_response(
        'account/signup_form.html', 
        {'form': form}
    )

    
    
