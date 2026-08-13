"""
Authentik OIDC login + authorization helpers.

Authentik ส่ง claim:
  role = "HR"   → สิทธิ์ HR
  (ค่าอื่น / ว่าง) → ไม่ใช่ HR

เก็บ role บน User ใน DB ตาม claim ตรง ๆ — ไม่ใส่ default
"""

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

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
    role = claim_str(claims, "role")# ข้อมูลมี Key ที่ชื่อ "role" ไหม ถ้ามีให้ดึงค่ามา
    return role.upper() if role else ""


# ---------------------------------------------------------------------------
# Authorization (ใช้ใน views)
# ---------------------------------------------------------------------------

def is_hr(request):
    """user.role == HR หรือไม่."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return False
    return (user.role or "").upper() == HR_ROLE


def require_hr(request):
    """True ถ้าเป็น HR หรือ superuser."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return False
    return is_hr(request) or user.is_superuser


def can_approve(user, requisition):
    """หัวหน้า (person_unid == approver_unid) หรือ HR / superuser อนุมัติแทนได้."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or (user.role or "").upper() == HR_ROLE:
        return True
    if not user.person_unid:
        return False
    return user.person_unid == requisition.approver_unid


def can_edit_requisition(user, requisition):
    """หัวหน้า / HR แก้ไขใบที่ยังรออนุมัติได้."""
    if requisition.status != requisition.Status.PENDING:
        return False
    return can_approve(user, requisition)


def can_view_requisition(request, requisition):
    """ดูใบคำขอได้ถ้าเป็น HR / superuser / ผู้สร้าง / ผู้อนุมัติ."""
    user = request.user
    if not user.is_authenticated:
        return False
    if is_hr(request) or user.is_superuser:
        return True
    if requisition.requester_id == user.id:
        return True
    return can_approve(user, requisition)


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
