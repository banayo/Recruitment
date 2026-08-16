from datetime import timedelta, timezone as dt_timezone
from email.utils import parseaddr
from uuid import uuid4

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


def interview_end(start):
    return start + timedelta(minutes=30)


def _fmt_dt(dt):
    return timezone.localtime(dt).strftime("%d/%m/%Y %H:%M")


def _ics_stamp(dt):
    return timezone.localtime(dt).astimezone(dt_timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _escape_ics(text):
    return (
        (text or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


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


def extra_interviewer_emails(application):
    return _split_emails(application.ccmail)


def interviewer_emails(application):
    emails = []
    primary = (application.interviewer_email or "").strip()
    if primary:
        emails.append(primary)
    for extra in extra_interviewer_emails(application):
        if extra.lower() not in {e.lower() for e in emails}:
            emails.append(extra)
    return emails


def build_interview_ics(application):
    start = application.appointment_date
    end = interview_end(start)
    title = application.position.title
    candidate = f"{application.candidate.first_name_th} {application.candidate.last_name_th}".strip()
    summary = _escape_ics(f"สัมภาษณ์ {candidate} — {title}")
    if application.is_online and application.meeting_link:
        location = _escape_ics(application.meeting_link)
        description = _escape_ics(f"สัมภาษณ์ออนไลน์ {application.meeting_link}")
    else:
        location = _escape_ics("สำนักงาน")
        description = _escape_ics("สัมภาษณ์ ณ สถานที่บริษัท")
    organizer = parseaddr(settings.DEFAULT_FROM_EMAIL)[1] or "hr@localhost"
    attendees = []
    names = (application.interviewer_names or "").strip()
    for i, email in enumerate(interviewer_emails(application)):
        cn = names if i == 0 else email
        attendees.append(
            f"ATTENDEE;CN={_escape_ics(cn)};RSVP=TRUE:mailto:{email}"
        )
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//HR2 ATS//Interview//TH",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:interview-{application.pk}-{uuid4().hex[:8]}@hr2",
        f"DTSTAMP:{_ics_stamp(timezone.now())}",
        f"DTSTART:{_ics_stamp(start)}",
        f"DTEND:{_ics_stamp(end)}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
        f"LOCATION:{location}",
        f"ORGANIZER;CN=HR:mailto:{organizer}",
        *attendees,
        "STATUS:CONFIRMED",
        "SEQUENCE:0",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    return "\r\n".join(lines)


def _context(application):
    start = application.appointment_date
    end = interview_end(start)
    return {
        "application": application,
        "candidate": application.candidate,
        "position_title": application.position.title,
        "start_display": _fmt_dt(start),
        "end_display": _fmt_dt(end),
    }


def send_candidate_interview_email(application):
    to_email = (application.candidate.email or "").strip()
    if not to_email:
        return False, "ผู้สมัครยังไม่มีอีเมล — ไม่ได้ส่งเมลแจ้งผู้สมัคร"
    ctx = _context(application)
    subject = f"นัดหมายการสัมภาษณ์งาน ตำแหน่ง {ctx['position_title']}"
    text_body = render_to_string("recruitment/email/interview_invite.txt", ctx)
    html_body = render_to_string("recruitment/email/interview_invite.html", ctx)
    cc_list = [
        email
        for email in interviewer_emails(application)
        if email.lower() != to_email.lower()
    ]
    mail = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
        cc=cc_list,
    )
    mail.attach_alternative(html_body, "text/html")
    mail.send(fail_silently=False)
    return True, to_email


def send_interview_calendar(application):
    recipients = list(interviewer_emails(application))
    hr_cal = (getattr(settings, "HR_CALENDAR_EMAIL", "") or "").strip()
    if not hr_cal:
        hr_cal = parseaddr(settings.DEFAULT_FROM_EMAIL)[1]
    if hr_cal and hr_cal not in recipients:
        recipients.append(hr_cal)
    if not recipients:
        return False, "ไม่มีอีเมลผู้สัมภาษณ์หรือปฏิทิน HR"

    ctx = _context(application)
    ics = build_interview_ics(application)
    mail = EmailMessage(
        subject=f"ปฏิทินนัดสัมภาษณ์ — {ctx['position_title']} / {application.candidate}",
        body=(
            f"นัดสัมภาษณ์ {application.candidate}\n"
            f"ตำแหน่ง {ctx['position_title']}\n"
            f"เริ่ม {ctx['start_display']} สิ้นสุด {ctx['end_display']}\n"
            "แนบไฟล์ .ics สำหรับใส่ในปฏิทิน"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    mail.attach(
        "interview.ics",
        ics.encode("utf-8"),
        "text/calendar; method=REQUEST; charset=UTF-8",
    )
    mail.send(fail_silently=False)
    return True, ", ".join(recipients)
