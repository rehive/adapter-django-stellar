class DisableCSRF(object):
    def process_request(self, request):
        if not request.META.get('HTTP_AUTHORIZATION', None):
            setattr(request, '_dont_enforce_csrf_checks', True)