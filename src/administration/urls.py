# IMPORTS
# ---------------------------------------------------------------------------------------------------------------------#
# conf.urls
from django.contrib import admin
from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView

from rest_framework import routers
from django.contrib.auth.views import password_reset_confirm

from administration import views

admin.autodiscover()


# LOGGING
# ---------------------------------------------------------------------------------------------------------------------#
import logging

logger = logging.getLogger('django')


# URLS
# ---------------------------------------------------------------------------------------------------------------------#
urlpatterns = patterns('',

                       #  JWT
                       url(r'^api-token-auth/', 'rest_framework_jwt.views.obtain_jwt_token'),
                       url(r'^api-token-verify/', 'rest_framework_jwt.views.verify_jwt_token'),

                       url(r'^accounts/', include('rest_auth.urls')),
                       url(r'^accounts/register/', include('rest_auth.registration.urls')),
                       )
