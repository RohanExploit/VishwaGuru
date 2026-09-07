"""Authentication for privileged operations.

Every endpoint in this service was publicly callable. For most of them that is
correct -- anonymous reporting is a feature of a civic platform, and abuse is
bounded by the rate limiter. Two are not:

  POST /api/grievances/{id}/escalate  reassigns a grievance to a different
                                      authority and writes an audit record
  POST /api/issues/{id}/verify        changes an issue's status

Both change state that officials act on, so both now require a key.

The design is deliberately small. There is no user table, no registration and
no password handling, because nothing in the product needs one yet: issues
carry a `user_email` for attribution only. Adding a full identity system to
protect two endpoints would be a larger attack surface than the one it closes.
`optional_user` exists so that when identity does arrive, callers can adopt it
without another refactor.

Fail closed: if ADMIN_API_KEY is unset the protected endpoints answer 503
rather than allowing the request. A missing secret must never read as
"no authentication required".
"""

from __future__ import annotations

import hmac
import logging
import os
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, status

logger = logging.getLogger(__name__)

ADMIN_API_KEY_ENV = "ADMIN_API_KEY"
JWT_SECRET_ENV = "JWT_SECRET"  # noqa: S105 - the NAME of an env var, not a secret
JWT_ALGORITHM = "HS256"

# A key shorter than this is almost certainly a placeholder rather than a
# generated secret, and accepting it would give a false sense of protection.
MIN_API_KEY_LENGTH = 32


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identity extracted from a bearer token."""

    email: str | None
    subject: str | None


def _configured_admin_key() -> str | None:
    key = os.getenv(ADMIN_API_KEY_ENV, "").strip()
    return key or None


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """Guard privileged endpoints with a shared administrative key.

    Compared with hmac.compare_digest rather than ==, so the comparison does
    not leak the key's length or contents through timing.
    """
    expected = _configured_admin_key()

    if expected is None:
        # Fail closed. An unset secret means the deployment is misconfigured,
        # not that the endpoint is open.
        logger.error(
            "%s is not set; refusing privileged request rather than allowing it.",
            ADMIN_API_KEY_ENV,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="This endpoint is not available: the server has no administrative key configured.",
        )

    if len(expected) < MIN_API_KEY_LENGTH:
        logger.error(
            "%s is shorter than %d characters; refusing privileged request.",
            ADMIN_API_KEY_ENV,
            MIN_API_KEY_LENGTH,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="This endpoint is not available: the configured administrative key is too weak.",
        )

    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-API-Key header is required for this operation.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return x_api_key


def optional_user(
    authorization: str | None = Header(default=None),
) -> AuthenticatedUser | None:
    """Decode a bearer token when one is supplied, for attribution only.

    Returns None when no token is present, so public endpoints keep working
    anonymously. A token that is present but invalid is rejected outright --
    silently treating a bad token as "anonymous" hides both client bugs and
    tampering.
    """
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be of the form 'Bearer <token>'.",
        )

    secret = os.getenv(JWT_SECRET_ENV, "").strip()
    if not secret:
        logger.error("%s is not set; cannot verify the supplied token.", JWT_SECRET_ENV)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token authentication is not configured on this server.",
        )

    try:
        claims = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired."
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not valid."
        ) from exc

    return AuthenticatedUser(email=claims.get("email"), subject=claims.get("sub"))


# Convenience aliases so routes read as documentation.
RequireApiKey = Depends(require_api_key)
OptionalUser = Depends(optional_user)
