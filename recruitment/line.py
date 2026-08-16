"""LINE Login — link LINE userId to the already-authenticated Django user."""

import json
import secrets
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

AUTHORIZE_URL = "https://access.line.me/oauth2/v2.1/authorize"
TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
PROFILE_URL = "https://api.line.me/v2/profile"


def line_configured():
    return bool(
        getattr(settings, "LINE_LOGIN_CHANNEL_ID", "")
        and getattr(settings, "LINE_LOGIN_CHANNEL_SECRET", "")
        and getattr(settings, "LINE_LOGIN_REDIRECT_URI", "")
    )


def build_authorize_url(state):
    params = {
        "response_type": "code",
        "client_id": settings.LINE_LOGIN_CHANNEL_ID,
        "redirect_uri": settings.LINE_LOGIN_REDIRECT_URI,
        "state": state,
        "scope": "profile openid",
    }
    return AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)


def new_state():
    return secrets.token_urlsafe(24)


def fetch_line_user_id(code):
    """Exchange authorization code for LINE userId. Returns str or raises ValueError."""
    body = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINE_LOGIN_REDIRECT_URI,
            "client_id": settings.LINE_LOGIN_CHANNEL_ID,
            "client_secret": settings.LINE_LOGIN_CHANNEL_SECRET,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            token_payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ValueError("แลก token จาก LINE ไม่สำเร็จ") from exc

    access_token = token_payload.get("access_token")
    if not access_token:
        raise ValueError("LINE ไม่ส่ง access_token")

    profile_req = urllib.request.Request(
        PROFILE_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(profile_req, timeout=15) as resp:
            profile = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ValueError("อ่านโปรไฟล์ LINE ไม่สำเร็จ") from exc

    user_id = (profile.get("userId") or "").strip()
    if not user_id:
        raise ValueError("LINE ไม่ส่ง userId")
    return user_id
