import json
import pickle
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

ATTACH_DIR = Path(__file__).resolve().parent / "static" / "file"
CANDIDATE_ATTACHMENTS = (
    "mapkarmarts.jpg",
    "FM-HMR-RC04_compressed.pdf",
)
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


def interview_end(start):
    return start + timedelta(minutes=30)


def _fmt_dt(dt):
    return timezone.localtime(dt).strftime("%d/%m/%Y %H:%M")


def _split_emails(value):
    seen = set()
    emails = []
    for part in (value or "").replace(";", ",").split(","):
        email = part.strip()
        key = email.lower()
        if email and key not in seen:
            seen.add(key)
            emails.append(email)
    return emails


def interviewer_emails(application):
    return _split_emails(
        ",".join(
            [
                application.interviewer_email or "",
                application.ccmail or "",
            ]
        )
    )


def send_candidate_interview_email(application):
    #ส่งเมลล์การสัมภาษณ์งานให้ผู้สมัคร
    to_email = (application.candidate.email or "").strip()
    if not to_email:
        return False, "ผู้สมัครยังไม่มีอีเมล — ไม่ได้ส่งเมลแจ้งผู้สมัคร"

    start = application.appointment_date
    ctx = {
        "application": application,
        "candidate": application.candidate,
        "position_title": application.position.title,
        "start_display": _fmt_dt(start),
    }
    mail = EmailMultiAlternatives(
        subject=f"นัดหมายการสัมภาษณ์งาน ตำแหน่ง {ctx['position_title']}",
        body=render_to_string("recruitment/email/interview_invite.txt", ctx),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
        cc=[
            email
            for email in interviewer_emails(application)
            if email.lower() != to_email.lower()
        ],
    )
    mail.attach_alternative(
        render_to_string("recruitment/email/interview_invite.html", ctx),
        "text/html",
    )
    for filename in CANDIDATE_ATTACHMENTS:
        path = ATTACH_DIR / filename
        if path.is_file():
            mail.attach_file(str(path))
    mail.send(fail_silently=False)
    return True, to_email


def _setting_path(name, default=""):
    raw = getattr(settings, name, "") or default
    path = Path(raw)
    if not path.is_absolute():
        path = settings.BASE_DIR / path
    if path.is_file():
        return path
    fallback = Path(__file__).resolve().parent / "secrets" / path.name
    if fallback.is_file():
        return fallback
    return path


def _save_token(token_file, creds):
    token_file.parent.mkdir(parents=True, exist_ok=True)
    with token_file.open("wb") as handle:
        pickle.dump(creds, handle)


def google_calendar_credentials(interactive=False):
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds_file = _setting_path(
        "GOOGLE_CALENDAR_CREDENTIALS", "recruitment/secrets/credentials.json"
    )
    if not creds_file.is_file():
        raise RuntimeError(f"ไม่พบไฟล์ Google credentials ที่ {creds_file}")

    payload = json.loads(creds_file.read_text(encoding="utf-8"))
    if payload.get("type") == "service_account":
        return service_account.Credentials.from_service_account_file(
            str(creds_file), scopes=GOOGLE_CALENDAR_SCOPES
        )

    token_file = _setting_path(
        "GOOGLE_CALENDAR_TOKEN", "recruitment/secrets/token.pickle"
    )
    creds = None
    if token_file.is_file():
        with token_file.open("rb") as handle:
            creds = pickle.load(handle)
    if creds and not getattr(creds, "valid", False) and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(token_file, creds)
        except RefreshError as exc:
            token_file.unlink(missing_ok=True)
            creds = None
            if not interactive:
                raise RuntimeError(
                    "token Google หมดอายุหรือถูกยกเลิก — "
                    "รัน docker compose exec -it web python manage.py google_calendar_auth"
                ) from exc
    if creds and getattr(creds, "valid", False):
        return creds
    if not interactive:
        raise RuntimeError(
            "ยังไม่ได้เชื่อม Google Calendar — "
            "รัน docker compose exec -it web python manage.py google_calendar_auth"
        )
    flow = InstalledAppFlow.from_client_secrets_file(
        str(creds_file), GOOGLE_CALENDAR_SCOPES
    )
    creds = flow.run_local_server(
        host="localhost",
        bind_addr="0.0.0.0",
        port=int(getattr(settings, "GOOGLE_CALENDAR_AUTH_PORT", 8080) or 8080),
        open_browser=False,
    )
    _save_token(token_file, creds)
    return creds


def create_interview_google_calendar(application):
    #สร้างการนัดหมายการสัมภาษณ์งานใน Google Calendar
    from googleapiclient.discovery import build

    calendar_id = (getattr(settings, "GOOGLE_HR_CALENDAR_ID", "") or "").strip()
    if not calendar_id:
        return False, "ยังไม่ได้ตั้ง GOOGLE_HR_CALENDAR_ID"
    if not application.appointment_date:
        return False, "ยังไม่มีวันเวลานัดสัมภาษณ์"

    start = timezone.localtime(application.appointment_date)
    end = timezone.localtime(interview_end(application.appointment_date))
    tzname = settings.TIME_ZONE
    guests = interviewer_emails(application)
    candidate = application.candidate
    if application.is_online and application.meeting_link:
        location = application.meeting_link
        format_note = f"สัมภาษณ์ออนไลน์\n{application.meeting_link}"
    else:
        location = "สำนักงาน"
        format_note = "สัมภาษณ์ ณ สถานที่บริษัท"

    event = {
        "summary": f"สัมภาษณ์ {candidate} — {application.position.title}",
        "description": (
            f"ผู้สมัคร: {candidate}\n"
            f"โทร: {candidate.phone_number}\n"
            f"ตำแหน่ง: {application.position.title}\n"
            f"ผู้สัมภาษณ์: {application.interviewer_names}\n"
            f"{format_note}"
        ),
        "location": location,
        "start": {"dateTime": start.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": tzname},
        "end": {"dateTime": end.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": tzname},
        "attendees": [{"email": email} for email in guests],
    }
    color = (getattr(settings, "GOOGLE_CALENDAR_COLOR_ID", "") or "").strip()
    if color:
        event["colorId"] = color

    created = (
        build("calendar", "v3", credentials=google_calendar_credentials())
        .events()
        .insert(calendarId=calendar_id, body=event, sendUpdates="all")
        .execute()
    )
    return True, created.get("htmlLink") or ", ".join(guests) or calendar_id


def create_start_work_google_calendar(application):
    from datetime import datetime, time

    from googleapiclient.discovery import build

    calendar_id = (getattr(settings, "GOOGLE_HR_CALENDAR_ID", "") or "").strip()
    if not calendar_id:
        return False, "ยังไม่ได้ตั้ง GOOGLE_HR_CALENDAR_ID"
    if not application.start_work_date:
        return False, "ยังไม่มีวันที่นัดเริ่มงาน"

    tzname = settings.TIME_ZONE
    start = timezone.make_aware(
        datetime.combine(application.start_work_date, time(hour=9, minute=0)),
        timezone.get_current_timezone(),
    )
    end = start + timedelta(hours=1)
    candidate = application.candidate
    attendees = []
    email = (candidate.email or "").strip()
    if email:
        attendees.append({"email": email})
    event = {
        "summary": f"เริ่มงาน {candidate} — {application.position.title}",
        "description": (
            f"ผู้สมัคร: {candidate}\n"
            f"โทร: {candidate.phone_number}\n"
            f"ตำแหน่ง: {application.position.title}\n"
            f"วันที่เริ่มงาน: {application.start_work_date.strftime('%d/%m/%Y')}"
        ),
        "location": "สำนักงาน",
        "start": {
            "dateTime": timezone.localtime(start).strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": tzname,
        },
        "end": {
            "dateTime": timezone.localtime(end).strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": tzname,
        },
        "attendees": attendees,
    }
    color = (getattr(settings, "GOOGLE_CALENDAR_COLOR_ID", "") or "").strip()
    if color:
        event["colorId"] = color
    created = (
        build("calendar", "v3", credentials=google_calendar_credentials())
        .events()
        .insert(calendarId=calendar_id, body=event, sendUpdates="all")
        .execute()
    )
    return True, created.get("htmlLink") or calendar_id
