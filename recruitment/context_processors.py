from .authz import get_oidc_groups, is_hr
from .models import Requisition


def recruitment_context(request):
    pending_approvals = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and user.person_unid:
        pending_approvals = Requisition.objects.filter(
            approver_unid=user.person_unid,
            status=Requisition.Status.PENDING,
        ).count()

    return {
        "oidc_groups": get_oidc_groups(request) if hasattr(request, "session") else [],
        "is_hr_user": is_hr(request) if hasattr(request, "session") else False,
        "pending_approvals_count": pending_approvals,
    }
