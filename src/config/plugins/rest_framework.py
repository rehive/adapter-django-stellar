import datetime

from rest_framework.pagination import PageNumberPagination

ANONYMOUS_USER_ID = -1

# JWT Token
# ---------------------------------------------------------------------------------------------------------------------
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=6000),
}

CORS_ORIGIN_ALLOW_ALL = True

REST_AUTH_SERIALIZERS = {
    'JWT_SERIALIZER': 'administration.serializers.JWTSerializer',
}

REST_USE_JWT = True

# REST FRAMEWORK ~ http://www.django-rest-framework.org/
# ---------------------------------------------------------------------------------------------------------------------
#  TODO: Figure out why custom exception handler is not working:
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    ),
    # 'EXCEPTION_HANDLER': 'wallet.exceptions.custom_exception_handler',
}

OLD_PASSWORD_FIELD_ENABLED = True
LOGOUT_ON_PASSWORD_CHANGE= False

from rest_framework.settings import reload_api_settings
reload_api_settings(setting='REST_FRAMEWORK', value=REST_FRAMEWORK)
