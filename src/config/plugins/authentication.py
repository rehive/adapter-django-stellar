from django.utils.encoding import force_text


def user_display(user):
    return force_text(user.email)

LOGIN_REDIRECT_URL = '/dashboard'
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/dashboard'
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_UNIQUE_EMAIL = False
ACCOUNT_USER_DISPLAY = user_display
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_UNIQUE_USERNAME = False
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""

