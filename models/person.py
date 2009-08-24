from django.db import models
import django.contrib.auth.models
from django.utils.encoding import smart_str
import sha
import random
from accounts import Account
from group import Group
from role import Role
from django.conf import settings
from parser import SimpleRoleParser


class Person(models.Model):
    
    SESSION_KEY = 'LOGGED_IN_PERSON_ID'
    
    class Admin:
        pass
    
    class Meta:
        app_label = 'account'
        unique_together = (
            ("username", "account"),
        )
    
    class FieldPermissions:
        role_set = 'account_admin'
            
    username = models.CharField(
        max_length = 30,
    )    
    
    account = models.ForeignKey(
        to = Account,
        editable = False,
    )
    group = models.ForeignKey(
        to = Group,
        blank = True,
        null = True,
    )
    first_name = models.CharField(
        max_length = 40,
    )    
    
    last_name = models.CharField(
        max_length = 40,
    )
    
    email = models.EmailField(
    )
    
    
    # I am going to hell for this.
    new_password = models.CharField(
        'new password', 
        max_length = 30,
        blank = True,
        null = True,
    )

    password = models.CharField(
        'password', 
        max_length = 128,
        editable = False,
    )
    
    role_set = models.ManyToManyField(
        to = Role,
        related_name = 'person_set',
        blank = True,
    ) 
    
 
    def save(self, *args, **kwargs):
        # If the password has been changed, handle it.
        if self.new_password:
            self.set_password(self.new_password)
            self.new_password = None
            
        return super(Person, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return self.username
    
    
    def set_password(self, raw_password):
        """
        Hashes the password w/ random salt and stores it.
        """
        salt = sha.new(str(random.random())).hexdigest()[:5]
        hsh = sha.new(salt + smart_str(raw_password)).hexdigest()
        self.password = '%s$%s' % (salt, hsh)

    def check_password(self, raw_password):
        """
        Hashes the password and compares it to stored value
        """
        salt, hsh = self.password.split('$')
        return hsh == sha.new(smart_str(salt + raw_password)).hexdigest()

    def reset_password(self, length=7):
        """
        Resets the password to a random string.
        """
        new_password = sha.new(str(random.random())).hexdigest()[:length]
        self.set_password(new_password)
        return new_password
        
    def send_email(self, subject, message, from_email=None):
        """
        Sends an e-mail to this Person.
        """
        from django.core.mail import send_mail
        send_mail(
            subject, 
            message, 
            from_email, 
            [self.email], 
            fail_silently = settings.EMAIL_FAIL_SILENTLY,
        )
            
            
        
    def login(self, request):
        """
        Save person.id in session.
        """
        request.session[self.SESSION_KEY] = self.id
        request.person = self

        
    @classmethod
    def authenticate(cls, username, account, password):
        """
        If the given credentials are valid, return a User object.
        """
        try:
            person = Person.objects.get(username = username, account = account)
            if person.check_password(password):
                return person
        except models.ObjectDoesNotExist:
            return None
                

    @classmethod
    def logout(cls, request):
        """
        Remove the authenticated user's ID from the request.
        """
        request.person = None
        try:
            del request.session[cls.SESSION_KEY]
        except KeyError:
            pass
    
    @classmethod
    def load_from_request(cls, request):
        """
        Returns the person with id = request.session[SESSION_KEY]
        """
        if cls.SESSION_KEY in request.session:
            try:
                person = Person.objects.get(
                    pk = request.session[cls.SESSION_KEY],
                    account = request.account,
                )
                request.person = person
                return person
            except models.ObjectDoesNotExist:
                return None
        
    def has_roles(self,roles_string):
        """
        Returns True/False whether user has roles 
        e.g. roles_string='(admin|super_admin)&quest'
        """
        if not roles_string:
            return True
        try:
            if self.group and self.group.has_roles(roles_string):
                return True
        except Group.DoesNotExist:
            pass
        p=SimpleRoleParser(roles_string)
        r=[role.name for role in self.role_set.all()]
        return p.has_roles(r)        
        
    def add_role(self, *names):
        """
        Adds each of the roles specified in names to the person.
        """
        for name in names:
            self.role_set.add(Role.objects.get(name=name))
        
    def can_be_destroyed(self):
        return not self.has_roles('account_admin')
                
        
    @property
    def roles(self):
        return [role.name for role in self.role_set.all()]
        
        
        
        
