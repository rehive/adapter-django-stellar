from logging import getLogger

from decimal import Decimal
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = getLogger('django')


class MoneyField(models.DecimalField):
    """Decimal Field with hardcoded precision of 28 and a scale of 18."""

    def __init__(self, verbose_name=None, name=None, max_digits=28,
                 decimal_places=18, **kwargs):
        super(MoneyField, self).__init__(verbose_name, name, max_digits, decimal_places, **kwargs)


class Asset(models.Model):
    code = models.CharField(max_length=12, null=True, blank=True)
    description = models.CharField(max_length=20, null=True, blank=True)
    issuer = models.CharField(max_length=200, null=True, blank=True)
    account_id = models.CharField(max_length=200, null=True, blank=True)
    symbol = models.CharField(max_length=6, null=True, blank=True)
    unit = models.CharField(max_length=15, null=True, blank=True)
    divisibility = models.IntegerField(default=2)
    metadata = JSONField(null=False, blank=True, default={})


# Log of all receive transactions processed.
class ReceiveTransaction(models.Model):
    STATUS = (
        ('Waiting', 'Waiting'),
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),  # Confirmed but not yet uploaded to rehive
        ('Complete', 'Complete'),  # Confirmed and uploaded to rehive
        ('Failed', 'Failed'),
    )
    user_account = models.ForeignKey('adapter.UserAccount')
    external_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    rehive_code = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    recipient = models.CharField(max_length=200, null=True, blank=True)
    amount = MoneyField(default=Decimal(0))
    asset = models.ForeignKey('adapter.Asset')
    issuer = models.CharField(max_length=200, null=True, blank=True)
    rehive_response = JSONField(null=True, blank=True, default={})
    status = models.CharField(max_length=24, choices=STATUS, null=True, blank=True, db_index=True)
    data = JSONField(null=True, blank=True, default={})
    metadata = JSONField(null=True, blank=True, default={})

    def upload_to_rehive(self):
        from .rehive_api import create_or_confirm_rehive_receive
        self.refresh_from_db()
        if not self.rehive_code:
            if self.status == 'Pending':
                create_or_confirm_rehive_receive.delay(self.id, confirm=False)
        else:
            if self.status == 'Confirmed':
                create_or_confirm_rehive_receive.delay(self.id, confirm=True)


# Log of all processed sends.
class SendTransaction(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Complete', 'Complete'),
    )
    TYPE = (
        ('send', 'Send'),
        ('receive', 'Receive'),
    )
    admin_account = models.ForeignKey('adapter.AdminAccount')
    external_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    rehive_code = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    recipient = models.CharField(max_length=200, null=True, blank=True)
    amount = MoneyField(default=Decimal(0))
    asset = models.ForeignKey('adapter.Asset')
    issuer = models.CharField(max_length=200, null=True, blank=True)
    rehive_request = JSONField(null=True, blank=True, default={})
    data = JSONField(null=True, blank=True, default={})
    metadata = JSONField(null=True, blank=True, default={})

    def save(self, *args, **kwargs):
        if not self.id:  # On create
            self.admin_account = AdminAccount.objects.get(default=True)
        return super(SendTransaction, self).save(*args, **kwargs)

    def execute(self):
        self.admin_account.send(self)


# Accounts for identifying Rehive users.
# Passive account, receive only.
class UserAccount(models.Model):
    rehive_id = models.CharField(max_length=100, null=True, blank=True)  # id for identifying user on rehive
    account_id = models.CharField(max_length=200, null=True, blank=True)  # crypto address
    admin_account = models.ForeignKey('adapter.AdminAccount')
    metadata = JSONField(null=True, blank=True, default={})

    def save(self, *args, **kwargs):
        if not self.id:  # On create
            logger.info('Fetching account_id.')
            self.admin_account = AdminAccount.objects.get(name='receive')
            self._new_account()
        return super(UserAccount, self).save(*args, **kwargs)

    def _new_account(self):
        from .api import Interface
        interface = Interface(account=self.admin_account)

        # Get and save user account ID:
        account_details = interface.get_user_account_details()
        self.account_id = account_details['account_id']
        self.metadata = account_details['details']

        return account_details

    def get_details(self):
        return {'account_id': self.account_id, 'details': self.metadata}

    def subscribe_to_hooks(self):
        from .api import WebhookReceiveInterface
        # Subscribe to webhooks for receive transactions:
        webhooks = WebhookReceiveInterface(account=self)
        webhooks.subscribe_to_all()


@receiver(post_save, sender=UserAccount, dispatch_uid="subscribe_to_receive_hooks")
def subscribe_to_receive_hooks(sender, instance, created, **kwargs):
    # Kwargs raw is used to check if data is loaded from fixtures.
    if created and not kwargs.get('raw', False):
        logger.info('Subscribing to webhooks for receive transactions')
        try:
            instance.subscribe_to_hooks()
        except:
            pass


# HotWallet/ Operational Accounts for sending or receiving on behalf of users.
# Admin accounts usually have a secret key to authenticate with third-party provider (or XPUB for key generation).
class AdminAccount(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    rehive_id = models.CharField(max_length=100, null=True, blank=True)  # id for identifying admin on rehive
    type = models.CharField(max_length=100, null=True, blank=True)  # some more descriptive info.
    secret = JSONField(null=True, blank=True, default={})  # crypto seed, private key or XPUB
    metadata = JSONField(null=True, blank=True, default={})
    default = models.BooleanField(default=False)

    def send(self, tx: SendTransaction) -> bool:
        from .api import Interface
        from .rehive_api import confirm_rehive_transaction
        """
        Initiates a send transaction using the Admin account.
        """
        interface = Interface(account=self)
        interface.send(tx)
        confirm_rehive_transaction(tx_id=tx.id, tx_type='send')
        return True

    # Return account id (e.g. Bitcoin address)
    def get_account_details(self) -> dict:
        from .api import Interface
        """
        Returns third party identifier of Admin account. E.g. Bitcoin address.
        """
        interface = Interface(account=self)
        return interface.get_account_details()

    def get_balance(self) -> int:
        from .api import Interface
        interface = Interface(account=self)
        return interface.get_account_balance()


class ReceiveWebhook(models.Model):
    webhook_type = models.CharField(max_length=50, null=True, blank=True)
    webhook_id = models.CharField(max_length=50, null=True, blank=True)
    user_account = models.ForeignKey(UserAccount)
    callback_url = models.CharField(max_length=150, blank=False)
