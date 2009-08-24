import urllib2
from xml.dom import minidom
from xml.parsers.expat import ExpatError
from datetime import date, timedelta
from time import strftime
from errors import PaymentRequestError, PaymentResponseError

def start_payment(url, login, password, token, amount, card_number, 
                  card_expires, first_name, last_name, period=1, 
                  trial_periods=1, start_date=None, total_periods=36, 
                  trial_amount=0):
    """
    Create a recurring payment
    """
    
    # The transaction will fail if the start date is earlier
    # than the date the transaction was recieved. However, I can't
    # find any info on timezones, etc in the ARM docs. So I'm just
    # adding a day to the default start date.
    start_date = (
        start_date or (date.today() + timedelta(1))
    ).strftime('%Y-%m-%d')
    
    return _make_request(
        url, 
        _populate(_start_payment_xml, **locals())
    )
    

def change_payment(url, login, password, gateway_token, amount):
    """
    Alters the amount of a recurring payment
    """
    return _make_request(
        url, 
        _populate(_change_payment_xml, **locals())
    )

def cancel_payment(url, login, password, gateway_token):
    """
    Cancels a recurring payment.
    """
    return _make_request(
        url, 
        _populate(_cancel_payment_xml, **locals())
    )

def _populate(template, **values):
    """
    Places values into an template. Used to create the
    xml requests sent to Authorize.net
    """
    for key in values:
        template = template.replace(
            '{{ %s }}' % str(key),
            str(values[key])
        )
    return template
def _make_request(url, content, content_type='text/xml'):
    """
    Sends the request xml to the payment gateway. Returns
    gateway_token on success.
    """
    request = urllib2.Request(
        url, 
        content, 
        {'Content-Type': content_type}
    )
    
    return _process_response(
        urllib2.urlopen(request).read()
    )
    
    
def _process_response(xml):
    """
    Parses the xml response from the payment gateway.
    On success, returns gateway_token. On failure, 
    it raises either PaymentRequestError or PaymentResponseError
    """
    try:
        dom = minidom.parseString(xml)
    except ExpatError:
        raise PaymentResponseError(xml)
    
    def text(node):
        return ''.join(
            [n.data for n in node.childNodes if n.nodeType == n.TEXT_NODE]
        )
    
    def get(tag_name, dom = dom):
        return [text(e) for e in dom.getElementsByTagName(tag_name)]
        
    def eq(tag_name, value):
        return get(tag_name)[0].strip().lower() == value.lower()
        
    try:
        if eq('resultCode', 'ok'):
            id = get('subscriptionId')
            return id[0] if id else True
        elif eq('resultCode', 'error'):
            raise PaymentRequestError(
                zip(get('code'), get('text'))
            )
    except IndexError:
        # Index error is raised if an expected
        # field is missing.
        pass
    
    raise PaymentResponseError(xml)
    
            
        
        
        

# Go ahead, make fun of me :)

_start_payment_xml = """<?xml version="1.0" encoding="utf-8"?> 
<ARBCreateSubscriptionRequest 
xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd"> 
  <merchantAuthentication> 
    <name>{{ login }}</name> 
    <transactionKey>{{ password }}</transactionKey> 
  </merchantAuthentication> 
  <refId>{{ token }}</refId> 
  <subscription>         
    <paymentSchedule> 
      <interval> 
        <length>{{ period }}</length> 
        <unit>months</unit> 
      </interval> 
      <startDate>{{ start_date }}</startDate> 
      <totalOccurrences>{{ total_periods }}</totalOccurrences> 
      <trialOccurrences>{{ trial_periods }}</trialOccurrences> 
    </paymentSchedule> 
    <amount>{{ amount }}</amount> 
    <trialAmount>{{ trial_amount }}</trialAmount> 
    <payment> 
      <creditCard> 
        <cardNumber>{{ card_number }}</cardNumber> 
        <expirationDate>{{ card_expires }}</expirationDate> 
      </creditCard> 
    </payment> 
    <billTo> 
      <firstName>{{ first_name }}</firstName> 
      <lastName>{{ last_name }}</lastName> 
    </billTo> 
  </subscription> 
</ARBCreateSubscriptionRequest> 
""" 


_change_payment_xml = """<?xml version="1.0" encoding="utf-8"?> 
<ARBUpdateSubscriptionRequest 
xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd"> 
  <merchantAuthentication> 
    <name>{{ login }}</name> 
    <transactionKey>{{ password }}</transactionKey> 
  </merchantAuthentication> 
  <subscriptionId>{{ gateway_token }}</subscriptionId> 
  <subscription> 
    <amount>{{ amount }}</amount> 
  </subscription> 
</ARBUpdateSubscriptionRequest> 
"""

_cancel_payment_xml = """<?xml version="1.0" encoding="utf-8"?>
<ARBCancelSubscriptionRequest 
xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd"> 
  <merchantAuthentication> 
    <name>{{ login }}</name> 
    <transactionKey>{{ password }}</transactionKey> 
  </merchantAuthentication> 
  <subscriptionId>{{ gateway_token }}</subscriptionId> 
</ARBCancelSubscriptionRequest>   
"""


if __name__ == '__main__':
    
    # Tests for the authorize_net payment module. These
    # are not a part of the main Account test suite because
    # they interact with the Authorize.net servers using
    # a test account. 
    
    from pprint import pprint
    import unittest
    import random
    import md5
    
    URL = 'https://apitest.authorize.net/xml/v1/request.api'
    LOGIN = 'YOUR LOGIN'
    PASSWORD = 'YOUR PASSWORD'
    
    class AuthorizeNetTests(unittest.TestCase):
    
        def random(self):
            return md5.new(str(random.random())).hexdigest()[:5]
        
        def test_start_payment_invalid(self):
            """
            Invalid request results in PaymentRequestError
            """
            try:
                start_payment(
                    url = URL, 
                    login = LOGIN, 
                    password = PASSWORD, 
                    token = '', 
                    amount = '', 
                    card_number = '', 
                    card_expires = '', 
                    first_name = '', 
                    last_name = '', 
                )
                assert False
            except PaymentRequestError, e:
                assert e.messages
                
        def test_change_payment_invalid(self):
            """
            Invalid request results in PaymentRequestError
            """
            try:
                change_payment(
                    url = URL, 
                    login = LOGIN, 
                    password = PASSWORD, 
                    gateway_token = '666',
                    amount = '99.99',
                )
                assert False
            except PaymentRequestError, e:
                assert e.messages
                
            
        def test_cancel_payment_invalid(self):
            """
            Invalid request results in PaymentRequestError
            """
            try:
                cancel_payment(
                    url = URL, 
                    login = LOGIN, 
                    password = PASSWORD, 
                    gateway_token = '666',
                )
                assert False
            except PaymentRequestError, e:
                assert e.messages
                
                
        def test_wrong_url(self):
            """
            Invalid response results in PaymentResponseError
            """
            try:
                cancel_payment(
                    url = 'https://test.authorize.net/gateway/transact.dll', 
                    login = '', 
                    password = '', 
                    gateway_token = '',
                )
                
                assert False
            except PaymentResponseError, e:
                assert e.response
                
                
                
        def test_start_change_stop(self):
            gateway_token = start_payment(
                url = URL, 
                login = LOGIN, 
                password = PASSWORD, 
                token = self.random(), 
                amount = '29.95', 
                card_number = '4111111111111111', 
                card_expires = '2008-08', 
                first_name = 'Test', 
                last_name = 'Testerson', 
            )
            assert 1 < len(gateway_token) < 14
            assert int(gateway_token)
            
            assert change_payment(
                url = URL, 
                login = LOGIN, 
                password = PASSWORD, 
                gateway_token = gateway_token,
                amount = '99.99',
            )
            
            assert cancel_payment(
                url = URL, 
                login = LOGIN, 
                password = PASSWORD, 
                gateway_token = gateway_token,
            )
                
            print gateway_token
            
    unittest.main()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
