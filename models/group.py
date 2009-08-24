from django.db import models
import django.contrib.auth.models
from django.utils.encoding import smart_str
import sha
import random
from accounts import Account
from role import Role
from parser import SimpleRoleParser


class Group(models.Model):
    
    class Admin:
        pass
    
    class Meta:
        app_label = 'account'
        unique_together = (
            ("name", "account"),
        )
    
    name = models.CharField(
        max_length = 30,
    )    
    
    account = models.ForeignKey(
        to = Account,
        editable = False,
    )
    
    role_set = models.ManyToManyField(
        to = Role,
        related_name = 'group_set',
        blank = True,
    ) 
    
    def __unicode__(self):
        return self.name
    
    
    def has_roles(self,roles_string):
        """
        Returns True/False whether user has roles 
        e.g. roles_string='(admin|super_admin)&quest'
        """
        if not roles_string:
            return True
        p=SimpleRoleParser(roles_string)
        r=[role.name for role in self.role_set.all()]
        return p.has_roles(r)        
        
        
