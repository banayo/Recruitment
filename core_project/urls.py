"""
URL configuration for core_project.
"""
from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.urls import include, path
from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView,
    OIDCLogoutView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # OIDC must stay public or login redirect / callback will loop or fail
    path(
        "oidc/callback/",
        login_not_required(OIDCAuthenticationCallbackView.as_view()),
        name="oidc_authentication_callback",
    ),
    path(
        "oidc/authenticate/",
        login_not_required(OIDCAuthenticationRequestView.as_view()),
        name="oidc_authentication_init",
    ),
    path(
        "oidc/logout/",
        login_not_required(OIDCLogoutView.as_view()),
        name="oidc_logout",
    ),
    path("", include("recruitment.urls")),
]
