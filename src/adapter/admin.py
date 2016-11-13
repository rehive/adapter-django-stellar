from django.contrib import admin

from .models import UserAccount, AdminAccount, ReceiveWebhook, ReceiveTransaction, SendTransaction


class CustomModelAdmin(admin.ModelAdmin):
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields]
        super(CustomModelAdmin, self).__init__(model, admin_site)


class UserAccountAdmin(CustomModelAdmin):
    pass


class AdminAccountAdmin(CustomModelAdmin):
    pass


class ReceiveWebhookAdmin(CustomModelAdmin):
    pass


class ReceiveTransactionAdmin(CustomModelAdmin):
    pass

class SendTransactionAdmin(CustomModelAdmin):
    pass

admin.site.register(SendTransaction, SendTransactionAdmin)
admin.site.register(ReceiveTransaction, ReceiveTransactionAdmin)
admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(AdminAccount, AdminAccountAdmin)
admin.site.register(ReceiveWebhook, ReceiveWebhookAdmin)
