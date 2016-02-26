# -*- coding: utf-8 -*-
import logging
import datetime
import requests
import xml.etree.ElementTree as ElementTree

logger = logging.getLogger(__name__)

def toDate(v):
    if v is None:
        return
    return datetime.datetime.strptime(v[0:v.find('+')], '%Y-%m-%d').date()


class FioAccount(object):
    date_start = None
    date_end = None
    opening_balance = None
    closing_balance = None
    year_list = None
    id_from = None
    id_to = None
    currency = None
    iban = None
    bic = None
    bank = None
    number = None

    id_list = None
    id_last_download = None

    def set(self, data):
        self.date_start = toDate(data.get('dateStart'))
        self.date_end = toDate(data.get('dateEnd'))
        self.opening_balance = data.get('openingBalance')
        self.closing_balance = data.get('closingBalance')
        self.year_list = data.get('yearList')
        self.id_from = data.get('idFrom')
        self.id_to = data.get('idTo')
        self.currency = data.get('currency')
        self.iban = data.get('iban')
        self.bic = data.get('bic')
        self.bank = data.get('bankId')
        self.number = data.get('accountId')
        self.id_list = data.get('idList')
        self.id_last_download = data.get('idLastDownload')

    def __str__(self):
        return "%s/%s" % (self.number, self.bank)

    def __repr__(self):
        return "<account number=%s bank=%s from=%s to=%s>" % (self.number, self.account, self.id_from, self.id_to)


class FioPayment(object):
    id = None
    account = None
    bank = None
    date = None
    amount = None
    currency = None
    ks = None
    vs = None
    ss = None
    message = None
    note = None

    def val(self, item, name):
        if name in item and item[name]:
            return item[name]['value']
        return None

    def __init__(self, data):
        #todo parse all data
        self.id = self.val(data, 'column22')
        self.account =  self.val(data, 'column2')
        self.bank = self.val(data, 'column3')
        self.date = toDate(self.val(data, 'column0'))
        self.amount = self.val(data, 'column1')
        self.currency = self.val(data, 'column14')
        self.ks = self.val(data, 'column4')
        self.vs = self.val(data, 'column5')
        self.ss = self.val(data, 'column6')
        self.message = self.val(data, 'column16')
        self.note = self.val(data, 'column25')

    def __repr__(self):
        return u'<payment id=%s account=%s bank=%s date=%s amount=%s>' % (self.id, self.account, self.bank, self.date, self.amount)


class FioResult(object):
    def __init__(self):
        self.account = FioAccount()
        self.transaction_list = []

    def setAccount(self, data):
        self.account.set(data)

    def setPayments(self, data):
        for item in data:
            self.transaction_list.append(FioPayment(item))

class Fio(object):
    MAX_COMMAND = 1000
    PERIOD_URL = 'https://www.fio.cz/ib_api/rest/periods/%(token)s/%(start)s/%(end)s/transactions.json'
    LAST_URL = 'https://www.fio.cz/ib_api/rest/last/%(token)s/transactions.json'
    SETLAST_URL = 'https://www.fio.cz/ib_api/rest/set-last-id/%(token)s/%(id)s/'
    SEND_URL = 'https://www.fio.cz/ib_api/rest/import/'

    HEADER = '<?xml version="1.0" encoding="UTF-8"?><Import xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.fio.cz/schema/importIB.xsd"><Orders>'
    FOOTER = '</Orders></Import>'
    DOMESTIC_PAYMENT = '''<DomesticTransaction><accountFrom>%(account_from)s</accountFrom>
<currency>%(currency)s</currency>
<amount>%(amount)s</amount>
<accountTo>%(account_to)s</accountTo>
<bankCode>%(bank_to)s</bankCode>
<ks>%(ks)s</ks>
<vs>%(vs)s</vs>
<ss>%(ss)s</ss>
<date>%(date)s</date>
<messageForRecipient>%(message)s</messageForRecipient>
<comment>%(comment)s</comment>
<paymentType>%(type)s</paymentType>
</DomesticTransaction>'''

    EURO_PAYMENT = '''<T2Transaction>
<accountFrom>1234562</accountFrom>
<currency>EUR</currency>
<amount>100.00</amount>
<accountTo>AT611904300234573201</accountTo>
<ks>0558</ks>
<vs>1234567890</vs>
<ss>1234567890</ss>
<bic>ABAGATWWXXX</bic>
<date>2013-04-25</date>
<comment>Erste Zahlung</comment>
<benefName>Hans Gruber</benefName>
<benefStreet>Gugitzgasse 2</benefStreet>
<benefCity>Wien</benefCity>
<benefCountry>AT</benefCountry>
<remittanceInfo1></remittanceInfo1>
<remittanceInfo2></remittanceInfo2>
<remittanceInfo3></remittanceInfo3>
<paymentType>431008</paymentType>
</T2Transaction>'''

    PAYMENT = '''<ForeignTransaction>
<accountFrom>1234562</accountFrom>
<currency>USD</currency>
<amount>100.00</amount>
<accountTo>PK36SCBL0000001123456702</accountTo>
<bic>ALFHPKKAXXX</bic>
<date>2013-04-25</date>
<comment>Payment a0315</comment>
<benefName>Amir Khan</benefName>
<benefStreet>Nishtar Rd 13</benefStreet>
<benefCity>Karachi</benefCity>
<benefCountry>PK</benefCountry>
<remittanceInfo1> Payment for hotel 032013</ remittanceInfo1>
<remittanceInfo2></ remittanceInfo2>
<remittanceInfo3></ remittanceInfo3>
<remittanceInfo4></ remittanceInfo4>
<detailsOfCharges>470502</detailsOfCharges>
<paymentReason>348</paymentReason>
</ForeignTransaction>'''


    def __init__(self, token):
        '''
        '''
        self.token = token
        self.domestic_payment_list = []
        self.euro_payment_list = []
        self.payment_list = []

    def last(self):
        '''
        Get new payment
        '''

        response = requests.get(self.LAST_URL % {'token': self.token})
        if response.status_code == requests.codes.ok:
            return self._parse(response.json())
        response.raise_for_status()

    def setLast(self, param):
        '''
        Set last payment by id pohybu

        :param param: id pohybu or date
        :type param: int or datetime or str

        '''

        if isinstance(param, datetime.datetime) or isinstance(param, datetime.date):
            param = param.strftime('%Y-%m-%d')

        elif not isinstance(param, int) and not isinstance(param, str) and isinstance(param, unicode):
            return False

        response = requests.get(self.SETLAST_URL % {'token': self.token, 'id': param})
        if response.status_code == requests.codes.ok:
            return True

        response.raise_for_status()

    def period(self, start, end):
        '''
        '''

        if isinstance(start, datetime.datetime) or isinstance(start, datetime.date):
            start = start.strftime('%Y-%m-%d')

        if isinstance(end, datetime.datetime) or isinstance(end, datetime.date):
            end = end.strftime('%Y-%m-%d')

        response = requests.get(self.PERIOD_URL % {'token': self.token, 'start': start, 'end': end})
        if response.status_code == requests.codes.ok:
            return self._parse(response.json())
        response.raise_for_status()


    def _parse(self, data):
        '''
        '''

        response = FioResult()
        response.setAccount(data['accountStatement']['info'])
        response.setPayments(data['accountStatement']['transactionList']['transaction'])
        return response

    def addDomesticPayment(self, amount, acount_to, bank_to, ks='', vs='', ss='', date=None, message='', comment='', currency='CZK', type='431001'):
        '''
        '''

        if date is None:
            date = datetime.datetime.now().date()

        self.domestic_payment_list.append({
                                            'amount': amount,
                                            'currency': currency,
                                            'account_to': acount_to,
                                            'bank_to': bank_to,
                                            'ks': ks,
                                            'vs': vs,
                                            'ss': ss,
                                            'date': date,
                                            'message': message,
                                            'comment': comment,
                                            'type': type,
                                            })
    def addEuroPayment(self):
        '''
        '''

        pass

    def addPayment(self):
        '''
        '''

        pass

    def send(self, account):
        '''
        '''

        transaction_list = {}
        counter = 0
        message = self.HEADER

        while self.domestic_payment_list:
            if counter == self.MAX_COMMAND:
                break

            transaction = self.domestic_payment_list.pop()
            counter += 1
            message += self.DOMESTIC_PAYMENT % {
                'account_from': account,
                'account_to': transaction['account_to'],
                'bank_to': transaction['bank_to'],
                'amount': transaction['amount'],
                'currency': transaction['currency'],
                'ks': transaction['ks'],
                'vs': transaction['vs'],
                'ss': transaction['ss'],
                'date': transaction['date'].strftime('%Y-%m-%d'),
                'message': transaction['message'],
                'comment': transaction['comment'],
                'type': transaction['type'],
                }


        while self.euro_payment_list:
            if counter == self.MAX_COMMAND:
                break

            transaction = self.euro_payment_list.pop()
            counter += 1
            message += ''

        while self.payment_list:
            if counter == self.MAX_COMMAND:
                break

            transaction = self.payment_list.pop()
            counter += 1
            message += ''

        if counter > 0:
            message += self.FOOTER
            self._send(message, transaction_list)

        return counter

    def _send(self, message, transaction_list):
        '''
        '''

        data = {'token': self.token, 'type': 'xml'}
        response = requests.post(self.SEND_URL, data=data, files={'file': message})

        if response.status_code == requests.codes.conflict:
            response.raise_for_status()

        tree = ElementTree.fromstring(response.content)
        code = tree.find('result/errorCode')

        if code.text == '0':
            return tree.find('result/idInstruction').text

        code = tree.find('result/errorCode')
        status = tree.find('result/status')
        message = tree.find('result/message')
        if message is not None:
            message = message.text

        raise Exception(code.text, status.text, message)
