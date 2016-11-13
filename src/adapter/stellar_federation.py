from collections import OrderedDict
from logging import getLogger

import requests
import toml
from django.conf import settings
from rest_framework.exceptions import MethodNotAllowed, ValidationError, ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import NotImplementedAPIError
from .models import UserAccount
from .permissions import AdapterGlobalPermission
from .throttling import NoThrottling

logger = getLogger('django')

STELLAR_WALLET_DOMAIN = 'rehive.com'


def get_federation_details(address):
    if '*' not in address:
        raise TypeError('Invalid federation address')
    user_id, domain = address.split('*')
    stellar_toml = requests.get('https://' + domain + '/.well-known/stellar.toml')
    url = toml.loads(stellar_toml.text)['FEDERATION_SERVER']
    params = {'type': 'name',
              'q': address}
    federation = requests.get(url=url, params=params).json()
    return federation


def address_from_domain(domain, code):
    logger.info('Fetching address from domain.')
    stellar_toml = requests.get('https://' + domain + '/.well-known/stellar.toml')
    currencies = toml.loads(stellar_toml.text)['CURRENCIES']

    for currency in currencies:
        if currency['code'] == code:
            logger.info('Address: %s' % (currency['issuer'],))
            return currency['issuer']


class StellarFederationView(APIView):
    allowed_methods = ('GET',)
    throttle_classes = (NoThrottling,)
    permission_classes = (AdapterGlobalPermission,)

    def post(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    def get(self, request, *args, **kwargs):
        if request.query_params.get('type') == 'name':
            address = request.query_params.get('q')
            if address:
                account_id = address
                operating_receive_address = getattr(settings, 'STELLAR_RECEIVE_ADDRESS')
                if UserAccount.objects.filter(account_id=account_id):
                    return Response(OrderedDict([('stellar_address', address),
                                                 ('account_id', operating_receive_address),
                                                 ('memo_type', 'text'),
                                                 ('memo', address.split('*')[0])]))
                else:
                    raise ValidationError('Stellar address does not exist.')
            else:
                raise ParseError('Invalid query parameter provided.')
        else:
            raise NotImplementedAPIError()