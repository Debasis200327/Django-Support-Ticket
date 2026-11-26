import uuid

class RequestAuditMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.audit_id = str(uuid.uuid4())
        response = self.get_response(request)
        response['X-Request-ID'] = request.audit_id
        return response
