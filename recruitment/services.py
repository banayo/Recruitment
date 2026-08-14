from django.db import transaction
from django.db.models import F

from .models import JobPosition, Requisition


@transaction.atomic
def approve_requisition(requisition, *, approved_headcount=None, position=None):
    """ขั้นหัวหน้า: ตั้ง manager_approved — ยังไม่ซิงก์โควตา."""
    if approved_headcount is None:
        approved_headcount = requisition.required_headcount

    requisition.status = Requisition.Status.MANAGER_APPROVED
    requisition.approved_headcount = approved_headcount
    if position is not None:
        requisition.position = position
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
    """ขั้น HR: ผูกตำแหน่ง ตั้ง hr_approved แล้วซิงก์โควตา."""
    requisition.position = position
    if approved_headcount is not None:
        requisition.approved_headcount = approved_headcount
    if not requisition.approved_headcount:
        requisition.approved_headcount = requisition.required_headcount
    requisition.status = Requisition.Status.HR_APPROVED
    _sync_headcount_quota(requisition)
    requisition.save()
    return requisition


def _sync_headcount_quota(requisition):
    if requisition.is_headcount_synced:
        return
    if requisition.status != Requisition.Status.HR_APPROVED:
        return
    if not requisition.position_id or requisition.approved_headcount <= 0:
        return

    JobPosition.objects.filter(pk=requisition.position_id).update(
        target_headcount=F("target_headcount") + requisition.approved_headcount
    )
    requisition.is_headcount_synced = True
