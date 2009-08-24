from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseForbidden
from django.views.generic.list_detail import object_list
import django.newforms as forms
from .. import helpers

 
def list(request, queryset, *args, **kwargs):
    """
    Generic list view that only lists objects belonging 
    to the current account.
    """
    return object_list(
        request,
        queryset.filter(account = request.account), 
        *args, 
        **kwargs
    )


def create(request, model, decorator = lambda x:x,
           post_save_redirect='', template_name=''):
    """
    Generic view for object creation. Automatically
    adds the current account to object.account, and 
    the current user to object.created_by.
    
    Uses a newforms form generated from the model.
    `decorator` is called on the form class to allow
    customization.
    """
    
    FormClass = decorator(
        forms.form_for_model(
            model,
            fields = get_allowed_fields(request, model),
        ),
        request,
    )
    
    template_name = template_name or _make_template_name(model, 'form')

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            record = form.save(commit = False)
            record.account = request.account
            record.created_by = request.person
            record.save()
            return HttpResponseRedirect(
                post_save_redirect or record.get_absolute_url()
            )
    else:
        form = FormClass()
    return render_to_response(
        template_name,
        context_instance = RequestContext(
            request,
            {'form': form}
        )
    )    
    

def edit(request, id, model, decorator = lambda x:x,
           post_save_redirect='', template_name=''):
    
    """
    Generic view for object editing. Will only edit
    objects belonging to current account.
    
    Uses a newforms form generated from the model.
    `decorator` is called on the form class to allow
    customization.
    """
    record = get_or_404(request, model, id)
    
    FormClass = decorator(
        forms.form_for_instance(
            record,
            fields = get_allowed_fields(request, model),
        ), 
        request,
        instance = record
    )
    
    template_name = template_name or _make_template_name(model, 'form')

    #import pdb; pdb.set_trace()
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            record = form.save()
            return HttpResponseRedirect(
                post_save_redirect or record.get_absolute_url()
            )
    else:
        form = FormClass()
    return render_to_response(
        template_name,
        context_instance = RequestContext(
            request,
            {
                'form': form,
            }
        )
    )    
    
def get_allowed_fields(request, model):
    """
    Returns a list of names for fields that the
    current user has permission to edit.
    """
    opts = model._meta
    fields = opts.fields + opts.many_to_many
    permissions = getattr(model, 'FieldPermissions', None)
    if not fields:
        return [f.name for f in fields]
    if not request.person:
        return []
    return [f.name 
            for f in fields 
            if request.person.has_roles(
                getattr(permissions, f.name, '')
            )]

def destroy(request, id, model, post_destroy_redirect, cancel_url='', template_name=''):
    """
    Generic view for object deletion. Will only destroy
    objects belonging to current account.
    """
    record = get_or_404(request, model, id)
    if not getattr(record, 'can_be_destroyed', lambda: True)():
        return HttpResponseForbidden('This record cannot be destroyed.')
        
    if request.method == "POST":
        if record in [request.account, request.person]:
            return HttpResponseForbidden()
            
        record.delete()
        return HttpResponseRedirect(
            post_destroy_redirect
        )
    else:
        return helpers.render(
            request,
            template_name or 'account/confirm_destroy.html',
            {
                'record': record,
                'cancel_url': cancel_url or post_destroy_redirect,
            }
        )
    
    

def _make_template_name(ModelClass, name):
    """
    Creates a template name like "appname/modelname_name.html"
    """
    return "%s/%s_%s.html" % (
        ModelClass._meta.app_label, 
        ModelClass._meta.object_name.lower(),
        name
    )
    

def get_or_404(request, model, id):
    """
    Get an object belonging to the current account, with
    id = id. Raises 404 if not found.
    """
    try:
        return model.objects.get(
            id = id,
            account = request.account,
        )
    except model.DoesNotExist:
        raise Http404
    