"""
Helper functions for defining SUBSCRIPTION_LEVELS
and SUBSCRIPTION_REGULATORS
"""
class Unlimited: 
    """
    When used like `resources = {'disk': Unlimited}`
    signifies that a resource is unlimited.
    """
    pass

def count(app_label, model_name):
    """
    Creates a subscription regulator function
    that sees how many Widget instances belong
    to an account. If it is under the maximum,
    return true. if over, return false.
    """
    def do_model_count(account, value):
        model = _model(app_label, model_name)
        return model.objects.filter(account = account).count() < value
    return do_model_count
    
    
def class_method(app_label, model_name, method):
    """
    Creates a subscription regulator function
    that calls ModelName.method(account). 
    If the returned value is < the resource value, 
    returns true.
    """
    def do_call_class_method(account, value):
        model = _model(app_label, model_name)
        return getattr(model, method)(account) < value
    return do_call_class_method


def _model(app_label, model_name):
    """ 
    Get a model class from app name and model name.
    We have to fetch models this way because you can't
    import a model into settings.py
    """
    from django.db.models.loading import get_model
    return get_model(app_label, model_name)














