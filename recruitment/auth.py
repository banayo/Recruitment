"""
Authentik OIDC login + authorization helpers.

Authentik ส่ง claim:
  role = "HR"   → สิทธิ์ HR
  (ค่าอื่น / ว่าง) → ไม่ใช่ HR (ผู้ใช้ทั่วไป / หัวหน้าตามสาย)

สิทธิ์แยกชัด:
  หัวหน้า (designated manager) = person_unid == requisition.approver_unid
  HR = claim role HR (หรือ superuser)
"""

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from .models import Requisition

HR_ROLE = "HR"


# ---------------------------------------------------------------------------
# Claim helpers
# ---------------------------------------------------------------------------

def claim_str(claims, *keys, default=""):
    """อ่านค่า claim เป็น string (ลองหลาย key ตามลำดับ)."""
    for key in keys:
        value = claims.get(key)
        if value is None:
            continue
        return str(value).strip()
    return default


def claim_role(claims):
    """อ่าน role จาก claim ตามที่ Authentik ส่งมา — ไม่ใส่ default."""
    role = claim_str(claims, "role")
    return role.upper() if role else ""


# ---------------------------------------------------------------------------
# Authorization (ใช้ใน views)
# ---------------------------------------------------------------------------

def user_is_hr(user):
    """True ถ้าเป็น HR หรือ superuser."""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return (getattr(user, "role", "") or "").upper() == HR_ROLE


def is_hr(request):
    """request.user เป็น HR หรือไม่ (ไม่รวม superuser — ใช้ user_is_hr / require_hr)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return False
    return (user.role or "").upper() == HR_ROLE


def require_hr(request):
    """True ถ้าเป็น HR หรือ superuser — ใช้ล็อกหน้า master / สิทธิ์ HR."""
    return user_is_hr(getattr(request, "user", None))


def is_designated_manager(user, requisition):
    """หัวหน้าตามสายรายงาน: person_unid ตรง approver_unid ของใบ."""
    if user is None or not user.is_authenticated:
        return False
    if not user.person_unid:
        return False
    return user.person_unid == requisition.approver_unid


def can_decide_requisition(user, requisition):
    """หัวหน้าหรือ HR อนุมัติขั้นหัวหน้าได้เมื่อใบยัง pending."""
    if requisition.status != Requisition.Status.PENDING:
        return False
    return is_designated_manager(user, requisition) or user_is_hr(user)


def can_reject_requisition(user, requisition):
    """หัวหน้าปฏิเสธได้ตอน pending; HR ปฏิเสธได้ถึงขั้นหัวหน้าอนุมัติแล้ว."""
    if requisition.status == Requisition.Status.PENDING:
        return is_designated_manager(user, requisition) or user_is_hr(user)
    if requisition.status == Requisition.Status.MANAGER_APPROVED:
        return user_is_hr(user)
    return False


def can_hr_finalize(user, requisition):
    """HR ผูกตำแหน่งและอนุมัติขั้นสุดท้ายได้ก่อน hr_approved."""
    if not user_is_hr(user):
        return False
    return requisition.status in (
        Requisition.Status.PENDING,
        Requisition.Status.MANAGER_APPROVED,
    )


def can_edit_requisition(user, requisition):
    """แก้รายละเอียดได้ตอน pending (หัวหน้า/HR) หรือตอนรอ HR (เฉพาะ HR)."""
    if requisition.status == Requisition.Status.PENDING:
        return is_designated_manager(user, requisition) or user_is_hr(user)
    if requisition.status == Requisition.Status.MANAGER_APPROVED:
        return user_is_hr(user)
    return False


def can_view_requisition(request, requisition):
    """ดูใบได้ถ้าเป็น HR / ผู้สร้าง / หัวหน้าของใบ."""
    user = request.user
    if not user.is_authenticated:
        return False
    if user_is_hr(user):
        return True
    if requisition.requester_id == user.id:
        return True
    return is_designated_manager(user, requisition)


def can_approve(user, requisition):
    """alias: หัวหน้าของใบ หรือ HR (ไม่เช็ค status — ใช้ในจุดที่เช็ค status แยก)."""
    return is_designated_manager(user, requisition) or user_is_hr(user)


# ---------------------------------------------------------------------------
# OIDC backend (JIT User)
# ---------------------------------------------------------------------------

class AuthentikOIDCBackend(OIDCAuthenticationBackend):
    """Login ด้วย Authentik แล้วสร้าง/อัปเดต User จาก claims รวม role."""

    def filter_users_by_claims(self, claims):
        sub = claim_str(claims, "sub")
        if not sub:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(authentik_sub=sub)

    def create_user(self, claims):
        person_unid = claim_str(claims, "person_unid")
        sub = claim_str(claims, "sub")
        if not person_unid or not sub:
            return None

        user = self.UserModel.objects.create_user(
            username=person_unid,
            email=claim_str(claims, "email"),
            authentik_sub=sub,
            person_unid=person_unid,
        )
        user.set_unusable_password()
        self.apply_claims(user, claims)
        user.save()
        return user

    def update_user(self, user, claims):
        self.apply_claims(user, claims)
        user.save()
        return user

    def apply_claims(self, user, claims):
        user.authentik_sub = claim_str(claims, "sub") or user.authentik_sub
        user.person_unid = claim_str(claims, "person_unid") or user.person_unid
        user.approve_code = claim_str(claims, "approve_code")
        user.gender = claim_str(claims, "gender")
        user.division = claim_str(claims, "division")
        user.department = claim_str(claims, "department")
        user.location = claim_str(claims, "location")
        user.nickname = claim_str(claims, "nickname")
        user.company_code = claim_str(claims, "company_code")
        user.role = claim_role(claims)
        user.first_name = claim_str(claims, "given_name")

        email = claim_str(claims, "email")
        if email:
            user.email = email
