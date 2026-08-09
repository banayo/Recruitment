"""Authorization helpers — roles from session oidc_groups only."""

HR_GROUP = "RECRUITMENT_HR"


def get_oidc_groups(request):
    groups = request.session.get("oidc_groups") or []
    if isinstance(groups, str):
        return [groups]
    return list(groups)


def normalize_group_name(group):
    if isinstance(group, dict):
        group = group.get("name") or group.get("id") or ""
    text = str(group).strip()
    if "/" in text:
        text = text.rstrip("/").split("/")[-1]
    return text.upper()


def is_hr(request):
    return any(normalize_group_name(g) == HR_GROUP for g in get_oidc_groups(request))


def can_approve(user, requisition):
    if not user.is_authenticated:
        return False
    return bool(user.person_unid) and user.person_unid == requisition.approver_unid


def can_view_requisition(request, requisition):
    user = request.user
    if not user.is_authenticated:
        return False
    if is_hr(request) or user.is_superuser:
        return True
    if requisition.requester_id == user.id:
        return True
    return can_approve(user, requisition)
