class MockGateway:
    """
    A mock gateway so that we don't have to call the
    real gateway during testing.
    """
    def __init__(self):
        self.reset()
        
    def start_payment(self, **kwargs):
        self.start_payment_called = True
        return self._respond(
            kwargs.get('error') or self.error_on_start, 
            '1000'
        )
    
    def change_payment(self, **kwargs):
        self.change_payment_called = True
        return self._respond(
            kwargs.get('error') or self.error_on_change, 
            True,
        )
    
    def cancel_payment(self, **kwargs):
        self.cancel_payment_called = True
        return self._respond(
            kwargs.get('error') or self.error_on_cancel, 
            True,
        )
    
    def _respond(self, error=None, value=None):
        if error or self.error:
            raise (error or self.error)('')
        else:
            return value
        
    def reset(self):
        for a in [
            'error', 
            'error_on_start', 
            'error_on_change', 
            'error_on_cancel',
            'start_payment_called', 
            'change_payment_called', 
            'cancel_payment_called',
        ]: setattr(self, a, None)
        

