"""
Django settings for core_project (Internal Recruitment System — Phase 1).
"""
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "mozilla_django_oidc",
    "recruitment",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "mozilla_django_oidc.middleware.SessionRefresh",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "recruitment.context_processors.recruitment_context",
            ],
        },
    },
]

WSGI_APPLICATION = "core_project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "hr2"),
        "USER": os.getenv("POSTGRES_USER", "hr2"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "hr2"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "recruitment.User"

AUTHENTICATION_BACKENDS = [
    "recruitment.auth.AuthentikOIDCBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "oidc_authentication_init"
LOGIN_REDIRECT_URL = "recruitment:home"
LOGOUT_REDIRECT_URL = "recruitment:home"

# Authentik OIDC — tokens stay in server-side Django session (not browser storage)
OIDC_RP_CLIENT_ID = os.getenv("OIDC_RP_CLIENT_ID", "")
OIDC_RP_CLIENT_SECRET = os.getenv("OIDC_RP_CLIENT_SECRET", "")
OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv("OIDC_OP_AUTHORIZATION_ENDPOINT", "")
OIDC_OP_TOKEN_ENDPOINT = os.getenv("OIDC_OP_TOKEN_ENDPOINT", "")
OIDC_OP_USER_ENDPOINT = os.getenv("OIDC_OP_USER_ENDPOINT", "")
OIDC_OP_ISSUER = os.getenv("OIDC_OP_ISSUER", "").rstrip("/") + (
    "/" if os.getenv("OIDC_OP_ISSUER") else ""
)
_oidc_jwks = os.getenv("OIDC_OP_JWKS_ENDPOINT", "")
if not _oidc_jwks and OIDC_OP_ISSUER:
    _oidc_jwks = OIDC_OP_ISSUER.rstrip("/") + "/jwks/"
OIDC_OP_JWKS_ENDPOINT = _oidc_jwks
OIDC_RP_SIGN_ALGO = os.getenv("OIDC_RP_SIGN_ALGO", "RS256")
OIDC_RP_SCOPES = os.getenv("OIDC_RP_SCOPES", "openid profile email")
OIDC_STORE_ACCESS_TOKEN = True
OIDC_STORE_ID_TOKEN = True
OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = int(
    os.getenv("OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS", "900")
)

# Guard against the common Authentik misconfig: .../application/o/jwks/
if OIDC_OP_JWKS_ENDPOINT.rstrip("/").endswith("/application/o/jwks"):
    raise ValueError(
        "OIDC_OP_JWKS_ENDPOINT is missing the Authentik application slug. "
        "Use https://<host>/application/o/<slug>/jwks/ "
        "(copy Issuer/JWKS from the Authentik Provider page)."
    )

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

