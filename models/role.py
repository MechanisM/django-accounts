from django.db import models
#from person import Person
from accounts import Account


class Role(models.Model):
    name = models.CharField(verbose_name = "Role name", max_length = 40)
    #persons = models.ManyToManyField(to=Person, related_name='persons')
    
    class Admin:
        pass
    
    class Meta:
        app_label = 'account'
    

    def __unicode__(self):
        return self.name

        
