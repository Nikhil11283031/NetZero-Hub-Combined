"""Business-rule errors for the solar service, rendered by the API as {"code", "detail"}.

The same error format as the recycling service, so the shared frontend can show any service's errors."""
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class ServiceError(Exception):
    status_code = 400
    code = "service_error"

    def __init__(self, message, **extra):
        super().__init__(message)
        self.message = message
        self.extra = extra


class NotEligible(ServiceError):
    status_code = 422
    code = "not_eligible"


class SlotUnavailable(ServiceError):
    status_code = 409
    code = "slot_unavailable"


class ChangeNotAllowed(ServiceError):
    status_code = 409
    code = "change_not_allowed"


def exception_handler(exc, context):
    if isinstance(exc, ServiceError):
        return Response({"code": exc.code, "detail": exc.message, **exc.extra}, status=exc.status_code)
    return drf_exception_handler(exc, context)
