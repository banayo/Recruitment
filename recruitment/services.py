from django.db import transaction
from django.db.models import F

from .models import JobPosition, Requisition


@transaction.atomic
def approve_requisition(requisition, *, approved_headcount=None, position=None):
    """
    Manager/HR approval. Headcount sync runs only when approved + position mapped
    and not yet synced.
    """
    if approved_headcount is None:
        approved_headcount = requisition.required_headcount

    requisition.status = Requisition.Status.APPROVED
    requisition.approved_headcount = approved_headcount
    if position is not None:
        requisition.position = position
    _sync_headcount_quota(requisition)
    requisition.save()
    return requisition


@transaction.atomic
def reject_requisition(requisition):
    requisition.status = Requisition.Status.REJECTED
    requisition.approved_headcount = 0
    requisition.save(update_fields=["status", "approved_headcount", "updated_at"])
    return requisition


@transaction.atomic
def map_position_and_sync(requisition, *, position, approved_headcount=None):
    """HR maps an official JobPosition after (or during) approval."""
    requisition.position = position
    if approved_headcount is not None:
        requisition.approved_headcount = approved_headcount
    if requisition.status == Requisition.Status.PENDING:
        requisition.status = Requisition.Status.APPROVED
        if not requisition.approved_headcount:
            requisition.approved_headcount = requisition.required_headcount
    _sync_headcount_quota(requisition)
    requisition.save()
    return requisition


def _sync_headcount_quota(requisition):
    if requisition.is_headcount_synced:
        return
    if requisition.status != Requisition.Status.APPROVED:
        return
    if not requisition.position_id or requisition.approved_headcount <= 0:
        return

    JobPosition.objects.filter(pk=requisition.position_id).update(
        target_headcount=F("target_headcount") + requisition.approved_headcount
    )
    requisition.is_headcount_synced = True
