from datetime import date, timedelta, datetime
import time
from django.test import TestCase
from account.models import Person, Account, Role, RecurringPayment
from account.models import recurring_payment
from account.lib.payment.errors import PaymentRequestError, PaymentResponseError
from account.tests.mocks.payment_gateway import MockGateway



class RecurringPaymentTests(TestCase):
    fixtures = ['test/accounts.json', 'test/people.json', 'test/roles.json']
    def setUp(self):
        recurring_payment.gateway = MockGateway()
        recurring_payment.gateway.reset()
    
    def test_creates_payment(self):
        account = Account.objects.get(pk=2)
        payment = RecurringPayment.create(
            account = account, 
            amount = 2999, 
            card_number = '4111111111111111', 
            card_expires = date.today(), 
            first_name = 'Bob', 
            last_name = 'Jones',
            error = None,
        )
        
        assert recurring_payment.gateway.start_payment_called
        assert not recurring_payment.gateway.change_payment_called
        assert not recurring_payment.gateway.cancel_payment_called
        
        assert payment.name == "Bob Jones"
        assert payment.number == '************1111'
        assert payment.amount == '$29.99'
        assert payment.account == account
        assert payment.period == 1
        assert payment.token == '2'
        assert payment.gateway_token == '1000'
        
    def test_does_not_create_payment(self):
        count = RecurringPayment.objects.count()
        account = Account.objects.get(pk=2)
        try:
            RecurringPayment.create(
                account = account, 
                amount = '', 
                card_number = '', 
                card_expires = date.today(), 
                first_name = '', 
                last_name = '',
                error = PaymentRequestError,
            )
            assert False
        except PaymentRequestError:
            pass
        
        assert count == RecurringPayment.objects.count()
        
        assert recurring_payment.gateway.start_payment_called
        assert not recurring_payment.gateway.change_payment_called
        assert not recurring_payment.gateway.cancel_payment_called
        
        
        
    def make_payment(self):
        return RecurringPayment(
            name = 'Bob Jones',
            period = 1,
            amount = '$10.00',
            number = '********1234',
            token = 2,
            gateway_token = '1000',
            account = Account.objects.get(pk=2),
        )
        
    def test_changes_payment(self):
        payment = self.make_payment()
        payment.change_amount(
            amount = '99.99', 
            error = None,
        )
        
        assert not recurring_payment.gateway.start_payment_called
        assert recurring_payment.gateway.change_payment_called
        assert not recurring_payment.gateway.cancel_payment_called
        
        assert payment.amount == '$99.99'
        
        
        
    def test_cancels_payment(self):
        payment = self.make_payment()
        payment.cancel(
            error = None,
        )
        
        assert not recurring_payment.gateway.start_payment_called
        assert not recurring_payment.gateway.change_payment_called
        assert recurring_payment.gateway.cancel_payment_called
        
        assert not payment.is_active()
        
        # Is there an easier way to do this?
        self.assertAlmostEqual(
            time.mktime(payment.cancelled_at.timetuple()),
            time.mktime(datetime.now().timetuple())
        )
            
            
        
    def test_is_expired(self):
        payment = self.make_payment()
        assert not payment.is_expired()
        
        payment.period = 1
        payment.active_on = date(2007, 3, 19)
        payment.cancelled_at = datetime(2007, 9, 23)
        assert payment.is_expired(when = datetime(2007, 10, 20))
        assert not payment.is_expired(when = datetime(2007, 10, 19))
        assert not payment.is_expired(when = datetime(2007, 10, 18))
        
        payment.period = 3
        assert payment.is_expired(when = datetime(2007, 12, 20))
        assert not payment.is_expired(when = datetime(2007, 12, 19))
        
        payment.period = 12
        assert payment.is_expired(when = datetime(2008, 3, 20))
        assert not payment.is_expired(when = datetime(2008, 3, 19))
        
        
        
        
        
        
        
        
        
        
        