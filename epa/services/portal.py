"""EPA entry points for the shared NetZero Hub login.

Django owns users and verifies its opaque tokens. The EPA services keep their
own records and ask Django for identity on every user request (no token cache).
"""
import hmac
import os

import httpx
from fastapi import Header, HTTPException

from .incidents import create_app as incident_app
from .licensing import create_app as licence_app


def verified_principal(authorization: str = Header(default="")):
    scheme, _, token = authorization.partition(" ")
    internal = os.environ.get("NZ_INTERNAL_TOKEN", "")
    if scheme == "Bearer" and internal and hmac.compare_digest(token, internal):
        return {"subject": "incident-service", "role": "internal"}
    if scheme != "Token" or not token or any(c.isspace() for c in token):
        raise HTTPException(401, "Sign in to NetZero Hub to access EPA services")

    try:
        response = httpx.get(
            os.environ["NZ_AUTH_URL"],
            headers={"Authorization": authorization, "Accept": "application/json"},
            timeout=4.0,
            follow_redirects=False,
            trust_env=False,
        )
    except (httpx.HTTPError, KeyError) as error:
        raise HTTPException(503, "NetZero Hub authentication is unavailable; retry shortly") from error

    if response.status_code in (401, 403):
        raise HTTPException(401, "Your session has ended. Sign in to NetZero Hub again")
    if response.status_code != 200:
        raise HTTPException(503, "NetZero Hub authentication is unavailable; retry shortly")
    try:
        user = response.json()
        user_id = user["id"]
        role = user["epa_role"]
        if type(user_id) is not int or user_id < 1 or role not in ("client", "officer"):
            raise ValueError("Invalid identity response")
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(503, "NetZero Hub returned an invalid identity response") from error
    return {"subject": f"django:{user_id}", "role": role,
            "name": user.get("full_name") or user.get("username") or f"User {user_id}"}


def _check_configuration():
    if not os.environ.get("NZ_AUTH_URL") or not os.environ.get("NZ_INTERNAL_TOKEN"):
        raise RuntimeError("Set NZ_AUTH_URL and NZ_INTERNAL_TOKEN for the shared portal")


def create_licensing_app():
    _check_configuration()
    return licence_app(identity_dependency=verified_principal)


def create_incident_app():
    _check_configuration()
    return incident_app(identity_dependency=verified_principal)
