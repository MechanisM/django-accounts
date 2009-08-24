from django.test import TestCase, Client
from django.core import mail

class IntegrationTest(TestCase):
    def assertState(self, method, path, causes, effects):
        """
        This assertation is used to test django views using
        a 'state' based approach
        
        The idea is for any method/path a specific combination
        of causes results in a specific combination of effects.
        
        Paramters
        =========
        method:  'GET' or 'POST' or 'GET/POST'
        path:    a path to a django view
        causes:  a list of functions that act upon the test
                 client and upon the request parameters
        effects: a list of functions which examine the response
                 for the fullfillment of certain criteria.  
        
        Callback Signatures
        ====================
        cause_callback(client, parameters): return (client, parameters)
        effect_callback(client, response, testcase): return None
        
        """
        def run(request_method):
            self.client = Client()
            parameters = {}
            mail.outbox = []        
            
            for cause in causes:
                self.client, parameters = cause(self.client, parameters)
            
            response = getattr(self.client, request_method)(path, parameters)
            
            for effect in effects:
                effect(self.client, response, self)
            
        # Parses  "GET" "POST" "GET/POST" etc..
        for m in method.lower().split('/'):
            run(m)
        
    
