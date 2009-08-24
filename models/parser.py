from operator import itemgetter


class SimpleRoleParser:
    """ Parses role string and evaluates whether use has role based permissions
    Typical usage in User/Person model as has_roles method for specific person:
    
    def has_roles(self,roles_string):
        p=RoleParser(roles_string)
        r=[role.name for role in self.role_set.all()]
        return p.has_roles(r)    
    """
    def __init__(self,s):
        """ e.g. s='(admin|super_admin)&guest'
        """
        self.__spec_chars=['|','&','(',')']
        s = s.replace(' ', '')
        self.role_query=s
        self.parsed_roles=self.__strip_roles(s)
    
    def __strip_roles(self,t):
        """ Returns array of roles from role query. 
        """
        for c in self.__spec_chars:
            t=t.replace(c,'|')
        roles={}
        for p in t.split('|'):
            roles[p]=len(p)
        x=self.__sortedDict(roles)
        x.reverse()
        return x

    def __sortedDict(self,adict):
        items = adict.items()
        items.sort()
        return [key for key, value in items if key != '']

    def has_roles(self,roles):
        """ Returns True/False info by evaluating expression
            e.g. roles=['admin', 'guest1']
        """
        r=self.role_query
        
        for p in self.parsed_roles:
            if p in roles:
                r=r.replace(p,'True')
            else:
                r=r.replace(p,'False')
        return eval(r)    




 


