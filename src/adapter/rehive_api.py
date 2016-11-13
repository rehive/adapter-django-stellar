import requests
from celery import shared_task

import logging

from django.conf import settings

from .utils import to_cents
from .models import ReceiveTransaction, SendTransaction, UserAccount

from .exceptions import PlatformRequestFailedError

logger = logging.getLogger('django')


@shared_task(bind=True, name='adapter.confirm_rehive_tx.task', max_retries=24, default_retry_delay=60 * 60)
def confirm_rehive_transaction(self, tx_id: int, tx_type: str):
    if tx_type == 'receive':
        tx = ReceiveTransaction.objects.get(id=tx_id)
    elif tx_type == 'send':
        tx = SendTransaction.objects.get(id=tx_id)
    else:
        raise TypeError('Invalid transaction type specified.')

    logger.info('Transaction update request.')

    # Update URL
    url = getattr(settings, 'REHIVE_API_URL') + '/admins/transactions/update/'

    # Add Authorization headers
    headers = {'Authorization': 'Token ' + getattr(settings, 'REHIVE_API_TOKEN')}

    try:
        # Make request
        r = requests.post(url, json={'tx_code': tx.rehive_code, 'status': 'Confirmed'}, headers=headers)

        if r.status_code in (200,201):
            tx.rehive_response = r.json()
            tx.status = 'Complete'
            tx.save()
        else:
            logger.info(headers)
            logger.info('Failed transaction update request: HTTP %s Error: %s' % (r.status_code, r.text))
            tx.rehive_response = {'status': r.status_code, 'data': r.text}
            tx.status = 'Failed'
            tx.save()

    except (requests.exceptions.RequestException, requests.exceptions.MissingSchema) as e:
        try:
            logger.info('Retry transaction update request due to connection error.')
            self.retry(countdown=5 * 60, exc=PlatformRequestFailedError)
        except PlatformRequestFailedError:
            logger.info('Final transaction update request failure due to connection error.')


@shared_task(bind=True, name='adapter.create_or_confirm_rehive_receive.task', max_retries=24, default_retry_delay=60 * 60)
def create_or_confirm_rehive_receive(self, tx_id: int, confirm: bool=False):
    tx = ReceiveTransaction.objects.get(id=tx_id)
    # If transaction has not yet been created, create it:
    if not tx.rehive_code:
        url = getattr(settings, 'REHIVE_API_URL') + '/admins/transactions/receive/'
        headers = {'Authorization': 'Token ' + getattr(settings, 'REHIVE_API_TOKEN')}

        try:
            # Make request:
            r = requests.post(url,
                              json={'recipient': tx.user_account.rehive_id,
                                    'amount': to_cents(tx.amount, 8),
                                    'currency': tx.currency.code,
                                    'issuer': tx.issuer,
                                    'metadata': tx.metadata,
                                    'from_reference': tx.external_id},
                              headers=headers)

            if r.status_code in (200, 201):
                tx.rehive_response = r.json()
                tx.rehive_code = tx.rehive_response['data']['tx_code']
                tx.status = 'Pending'
                tx.save()
            else:
                logger.info(headers)
                logger.info('Failed transaction update request: HTTP %s Error: %s' % (r.status_code, r.text))
                tx.status = 'Failed'
                tx.rehive_response = {'status': r.status_code, 'data': r.text}
                tx.save()

        except (requests.exceptions.RequestException, requests.exceptions.MissingSchema) as e:
            try:
                logger.info('Retry transaction update request due to connection error.')
                self.retry(countdown=5 * 60, exc=PlatformRequestFailedError)
            except PlatformRequestFailedError:
                logger.info('Final transaction update request failure due to connection error.')

    # After creation, or if tx already exists, confirm it if necessary
    if confirm:
        logger.info('Transaction update request.')

        # Update URL
        url = getattr(settings, 'REHIVE_API_URL') + '/admins/transactions/update/'

        # Add Authorization headers
        headers = {'Authorization': 'Token ' + getattr(settings, 'REHIVE_API_TOKEN')}

        try:
            # Make request
            r = requests.post(url, json={'tx_code': tx.rehive_code, 'status': 'Confirmed'}, headers=headers)

            if r.status_code in (200, 201):
                tx.rehive_response = r.json()
                tx.status = 'Complete'
                tx.save()
            else:
                logger.info(headers)
                logger.info('Failed transaction update request: HTTP %s Error: %s' % (r.status_code, r.text))
                tx.rehive_response = {'status': r.status_code, 'data': r.text}
                tx.status = 'Failed'
                tx.save()

        except (requests.exceptions.RequestException, requests.exceptions.MissingSchema) as e:
            try:
                logger.info('Retry transaction update request due to connection error.')
                self.retry(countdown=5 * 60, exc=PlatformRequestFailedError)
            except PlatformRequestFailedError:
                logger.info('Final transaction update request failure due to connection error.')
