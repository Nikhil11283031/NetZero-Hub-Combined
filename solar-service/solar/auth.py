"""Sign-in for the solar microservice.

User accounts live in the group's Django backend (one login for the whole NetZero Hub). Solar never reads that
database: for each request it sends the caller's token to GET /api/v1/auth/me/ (NZ_AUTH_URL) and uses the
answer (id, username, name, is_staff), the same way the EPA services verify identity. Redirects are not
followed. Answers are not cached unless AUTH_CACHE_SECONDS is set, so signing out takes effect immediately.
"""
import hashlib
import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.cache import cache
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header


class ServiceUnavailable(exceptions.APIException):
    status_code = 503
    default_detail = "The sign-in service is not available right now. Please try again shortly."
    default_code = "auth_unavailable"


class RemoteUser:
    """The signed-in user as described by the group accounts service (Django backend)."""

    is_authenticated = True
    is_anonymous = False

    def __init__(self, data):
        self.id = self.pk = data["id"]
        self.username = data.get("username", "")
        self.email = data.get("email", "")
        self.first_name = data.get("first_name", "")
        self.last_name = data.get("last_name", "")
        self.is_staff = bool(data.get("is_staff", False))

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.username


class _RefuseRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # a redirect is treated as an error, never followed


_NO_REDIRECTS = urllib.request.build_opener(_RefuseRedirects)


def fetch_user(token):
    """Ask the accounts service who owns this token. Returns the user data, or None if the token is invalid."""
    req = urllib.request.Request(
        settings.NZ_AUTH_URL,
        headers={"Authorization": f"Token {token}", "Accept": "application/json"},
    )
    try:
        with _NO_REDIRECTS.open(req, timeout=5) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as err:
        if err.code in (401, 403):
            return None
        raise ServiceUnavailable() from err
    except (urllib.error.URLError, TimeoutError, ValueError) as err:
        raise ServiceUnavailable() from err


class RemoteTokenAuthentication(BaseAuthentication):
    """Accepts the same "Authorization: Token <key>" header as the recycling service."""

    keyword = "Token"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != self.keyword.lower().encode():
            return None
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed("Invalid token header.")
        token = parts[1].decode()

        key = "solar-auth:" + hashlib.sha256(token.encode()).hexdigest()
        data = cache.get(key) if settings.AUTH_CACHE_SECONDS else None
        if data is None:
            data = fetch_user(token)
            if data is None:
                raise exceptions.AuthenticationFailed("Invalid or expired token.")
            if settings.AUTH_CACHE_SECONDS:
                cache.set(key, data, settings.AUTH_CACHE_SECONDS)
        return RemoteUser(data), token

    def authenticate_header(self, request):
        return self.keyword


try:  # Describe the token header in the API docs (drf-spectacular).
    from drf_spectacular.extensions import OpenApiAuthenticationExtension

    class RemoteTokenScheme(OpenApiAuthenticationExtension):
        target_class = "solar.auth.RemoteTokenAuthentication"
        name = "tokenAuth"

        def get_security_definition(self, auto_schema):
            return {"type": "apiKey", "in": "header", "name": "Authorization",
                    "description": 'Token from the accounts service login, sent as "Token <key>".'}
except ImportError:  # pragma: no cover
    pass
