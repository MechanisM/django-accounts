from django import template
from django.template import resolve_variable
import sys

register = template.Library()


def make_parser(NodeClass, name):
    """
    This factory makes parser functions that
    use the syntax {% name "arg" %} content {% endname %}
    """
    def the_parser(parser, token):
        try:
            tag, arg = token.split_contents()
        except ValueError:
            raise template.TemplateSyntaxError("Tag '%s' requires 1 argument." % name)
        arg = arg.replace('"', '')
        nodelist = parser.parse(('end' + name,))
    
        parser.delete_first_token()
        return NodeClass(arg, nodelist)
    
    setattr(
        sys.modules[__name__], 
        name, 
        register.tag(name)(the_parser)
    )
    
class ShowHideNode(template.Node):
    """
    Base node which either shows or hides
    its content based on the return value
    of self._show
    """
    def __init__(self, arg, nodelist):
        self.arg = arg
        self.nodelist = nodelist
    def render(self, context):
        return self.nodelist.render(context) if self._show(context) else ''
    def _show(self):
        return True
        
class RoleCheckNode(ShowHideNode):
    """
    Shows content if person in context has a certain role
    """
    def _show(self, context):
        person = resolve_variable('person', context)
        return person and person.has_roles(self.arg)
        
class GroupCheckNode(ShowHideNode):
    """
    Shows content if person in context has a certain group
    """
    def _show(self, context):
        person = resolve_variable('person', context)
        return person and getattr(person.group, 'name', '').lower() == self.arg.lower()
    
class PersonLoggedInCheckNode(ShowHideNode):
    """
    Shows content if there is a person in the context.
    """
    def _show(self, context):
        return resolve_variable('person', context)
    
    
class SubscriptionLevelCheckNode(ShowHideNode):
    """
    Shows content if account in context has a certain
    subscription level
    """
    def _show(self, context):
        account = resolve_variable('account', context)
        return account.has_level(self.arg)
    
class SubscriptionLevelOrGreaterCheckNode(ShowHideNode):
    """
    Shows content if account in context has a certain
    subscription level, (or one greater)
    """
    def _show(self, context):
        account = resolve_variable('account', context)
        return account.has_level_or_greater(self.arg)
    
class ResourceCheckNode(ShowHideNode):
    """
    Shows content if account in context has a certain
    resource available
    """
    def _show(self, context):
        account = resolve_variable('account', context)
        return account.has_resource(self.arg)
    
class RequiresPaymentCheckNode(ShowHideNode):
    """
    Shows content if account in context has a certain
    subscription level
    """
    def _show(self, context):
        account = resolve_variable('account', context)
        return account.requires_payment()
    
    
    
make_parser(RoleCheckNode, 'ifrole')
make_parser(GroupCheckNode, 'ifgroup')
make_parser(PersonLoggedInCheckNode, 'ifpersonloggedin')
make_parser(SubscriptionLevelCheckNode, 'iflevel')
make_parser(SubscriptionLevelOrGreaterCheckNode, 'iflevelmin')
make_parser(ResourceCheckNode, 'ifresource')




@register.simple_tag
def postlink(url, label):
    return """
        <form class="postlink" method="POST" action="%s">
                <input id="account_logout" type="SUBMIT" value="%s"/>
        </form>
    """ % (label, url)









