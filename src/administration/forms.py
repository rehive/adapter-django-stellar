from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _


class CustomSignupForm(forms.Form):

    first_name = forms.CharField(label=_("First name"), max_length=30, required=True)

    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.save()
