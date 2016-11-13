import urllib.parse
from collections import OrderedDict

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework.generics import GenericAPIView
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from .api import process_webhook_receive
from .utils import from_cents, input_to_json
from .api import Interface
from .models import UserAccount, AdminAccount, SendTransaction, Currency, Asset
from .permissions import AdapterGlobalPermission

from logging import getLogger

from .throttling import NoThrottling

from .serializers import TransactionSerializer, UserAccountSerializer, AddAssetSerializer

logger = getLogger('django')


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def adapter_root(request, format=None):
    """
    ### Notes:

    To make use of this adapter:

    1) Set the Rehive webhooks for each tx type to match their corresponding endpoints below.

    2) Set a secret key for each transaction webhook

    3) Ensure the the required ENV variables have been added to the server.

    **Required ENV variables:**

    In order to use the  adapter you must set the following ENV variables on the server.

    `REHIVE_API_TOKEN` : Secret Key for authenticating with Rehive for admin functions.

    `REHIVE_API_URL` : Rehive API URL

    `ADAPTER_SECRET_KEY`: Secret Key for adapter endpoints.

    ---

    """

    return Response({'Purchase': reverse('adapter-api:purchase',
                                         request=request,
                                         format=format),
                     'Withdraw': reverse('adapter-api:withdraw',
                                         request=request,
                                         format=format),
                     'Deposit': reverse('adapter-api:deposit',
                                        request=request,
                                        format=format),
                     'Send': reverse('adapter-api:send',
                                     request=request,
                                     format=format),
                     })


class PurchaseView(GenericAPIView):
    allowed_methods = ('POST',)
    throttle_classes = (NoThrottling,)
    serializer_class = TransactionSerializer
    permission_classes = (AdapterGlobalPermission,)

    def post(self, request, *args, **kwargs):
        return Response({'status': 'success'})

    def get(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('GET')


class WithdrawView(GenericAPIView):
    allowed_methods = ('POST',)
    throttle_classes = (NoThrottling,)
    serializer_class = TransactionSerializer
    permission_classes = (AdapterGlobalPermission,)

    def post(self, request, *args, **kwargs):
        return Response({'status': 'success'})

    def get(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('GET')


class DepositView(GenericAPIView):
    allowed_methods = ('POST',)
    throttle_classes = (NoThrottling,)
    serializer_class = TransactionSerializer
    permission_classes = (AdapterGlobalPermission,)

    def post(self, request, *args, **kwargs):
        return Response({'status': 'success'})

    def get(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('GET')


class SendView(GenericAPIView):
    allowed_methods = ('POST',)
    throttle_classes = (NoThrottling,)
    serializer_class = TransactionSerializer
    authentication_classes = []
    permission_classes = (AdapterGlobalPermission,)

    def post(self, request, *args, **kwargs):
        logger.info('Received send request')
        tx_code = request.data.get('tx_code')
        to_user = request.data.get('to_user')
        amount = from_cents(request.data.get('amount'), 8)
        currency = request.data.get('currency')
        issuer = request.data.get('issuer')

        logger.debug(request.data)
        logger.info('To: ' + to_user)
        logger.info('Amount: ' + str(amount))
        logger.info('Currency: ' + currency)

        asset = Asset.objects.get_or_create(code=currency)
        tx = SendTransaction.objects.create(rehive_code=tx_code,
                                            recipient=to_user,
                                            amount=amount,
                                            asset=asset,
                                            issuer=issuer)
        if tx.currency == 'XBT':
            tx.execute()

        return Response({'status': 'success'})

    def get(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('GET')


class BalanceView(APIView):
    allowed_methods = ('GET',)
    throttle_classes = (NoThrottling,)
    permission_classes = (AllowAny, AdapterGlobalPermission,)

    def post(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('POST')

    def get(self, request, *args, **kwargs):
        account = AdminAccount.objects.get(default=True)
        interface = Interface(account=account)
        balance_details = interface.get_account_balance()
        return Response({'balance': balance_details})


class OperatingAccountView(APIView):
    allowed_methods = ('GET',)
    throttle_classes = (NoThrottling,)
    permission_classes = (AdapterGlobalPermission,)

    def post(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('POST')

    def get(self, request, *args, **kwargs):
        account = AdminAccount.objects.get(default=True)
        interface = Interface(account=account)
        details = interface.get_account_details()
        return Response(details)


class UserAccountView(GenericAPIView):
    allowed_methods = ('POST',)
    throttle_classes = (NoThrottling,)
    permission_classes = (AdapterGlobalPermission,)
    serializer_class = UserAccountSerializer

    def post(self, request, *args, **kwargs):
        logger.info('User account requested.')
        logger.info(request.data)
        user_id = request.data.get('user_id')
        # Check if metadata is specified:
        metadata = input_to_json(request.data.get('metadata'))

        # Get Account ID:
        user_account, created = UserAccount.objects.get_or_create(rehive_id=user_id)

        interface = Interface(account=user_account)

        details = interface.get_user_account_details()

        return Response(details)

    def get(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('GET')


class WebhookView(APIView):
    allowed_methods = ('POST',)
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        receive_id = request.GET.get('id', '')
        hook_name = self.kwargs.get('hook_name')
        data = request.data

        logger.info('Webhook received')
        logger.debug(data)

        if not receive_id:
            raise Exception('Bad blockcypher post: no receive_id')

        process_webhook_receive.delay(webhook_type=hook_name,
                                      receive_id=receive_id,
                                      data=data)

        return Response({}, status=HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        return Response({}, status=HTTP_404_NOT_FOUND)


class AddAssetView(GenericAPIView):
    allowed_methods = ('POST',)
    throttle_classes = (NoThrottling,)
    permission_classes = (AdapterGlobalPermission,)
    serializer_class = AddAssetSerializer

    def post(self, request, *args, **kwargs):
        asset_code = request.data.get('code')
        issuer = request.data.get('issuer')

        # Get Metadata:
        metadata = input_to_json(request.data.get('metadata'))

        account = AdminAccount.objects.get(default=True)
        interface = Interface(account=account)

        issuer_details = interface.get_or_create_asset(issuer, asset_code, metadata)

        return Response({'status': 'success', 'data': issuer_details})

    def get(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('GET')