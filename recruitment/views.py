from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .authz import can_approve, can_view_requisition, is_hr
from .forms import HRMapForm, RequisitionCreateForm, RequisitionDecideForm
from .models import Requisition
from .services import approve_requisition, map_position_and_sync, reject_requisition


def home(request):
    return render(request, "recruitment/home.html")


@login_required
def requisition_list(request):
    if is_hr(request) or request.user.is_superuser:
        qs = Requisition.objects.select_related("requester", "position")
    else:
        qs = Requisition.objects.filter(requester=request.user).select_related(
            "requester", "position"
        )
    return render(
        request,
        "recruitment/requisition_list.html",
        {"requisitions": qs},
    )


@login_required
def requisition_create(request):
    if request.method == "POST":
        form = RequisitionCreateForm(request.POST)
        if form.is_valid():
            requisition = form.save(commit=False)
            requisition.requester = request.user
            requisition.approver_unid = request.user.approve_code
            requisition.status = Requisition.Status.PENDING
            if not requisition.approver_unid:
                messages.error(
                    request,
                    "บัญชีของคุณยังไม่มีรหัสผู้อนุมัติ (approve_code) จาก Authentik",
                )
            else:
                requisition.save()
                messages.success(request, "สร้างคำขออัตรากำลังแล้ว ส่งให้หัวหน้าอนุมัติ")
                return redirect("recruitment:requisition_detail", pk=requisition.pk)
    else:
        form = RequisitionCreateForm()

    return render(request, "recruitment/requisition_form.html", {"form": form})


@login_required
def requisition_detail(request, pk):
    requisition = get_object_or_404(
        Requisition.objects.select_related("requester", "position"),
        pk=pk,
    )
    if not can_view_requisition(request, requisition):
        return HttpResponseForbidden("ไม่มีสิทธิ์ดูคำขอนี้")

    decide_form = None
    hr_form = None
    if (
        requisition.status == Requisition.Status.PENDING
        and can_approve(request.user, requisition)
    ):
        decide_form = RequisitionDecideForm(requisition=requisition)
    if is_hr(request) or request.user.is_superuser:
        hr_form = HRMapForm(requisition=requisition)

    return render(
        request,
        "recruitment/requisition_detail.html",
        {
            "requisition": requisition,
            "decide_form": decide_form,
            "hr_form": hr_form,
            "can_decide": decide_form is not None,
            "is_hr_user": is_hr(request) or request.user.is_superuser,
        },
    )


@login_required
def approval_inbox(request):
    qs = (
        Requisition.objects.filter(
            approver_unid=request.user.person_unid,
            status=Requisition.Status.PENDING,
        )
        .select_related("requester", "position")
        .order_by("-created_at")
    )
    return render(request, "recruitment/approval_inbox.html", {"requisitions": qs})


@login_required
@require_POST
def requisition_approve(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    if requisition.status != Requisition.Status.PENDING:
        messages.error(request, "คำขอนี้ไม่อยู่ในสถานะรออนุมัติ")
        return redirect("recruitment:requisition_detail", pk=pk)
    if not can_approve(request.user, requisition) and not (
        is_hr(request) or request.user.is_superuser
    ):
        return HttpResponseForbidden("ไม่มีสิทธิ์อนุมัติคำขอนี้")

    form = RequisitionDecideForm(request.POST, requisition=requisition)
    if not form.is_valid():
        messages.error(request, "ข้อมูลอนุมัติไม่ถูกต้อง")
        return redirect("recruitment:requisition_detail", pk=pk)

    approved_headcount = form.cleaned_data.get("approved_headcount") or requisition.required_headcount
    approve_requisition(requisition, approved_headcount=approved_headcount)
    messages.success(request, "อนุมัติคำขอแล้ว")
    return redirect("recruitment:requisition_detail", pk=pk)


@login_required
@require_POST
def requisition_reject(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    if requisition.status != Requisition.Status.PENDING:
        messages.error(request, "คำขอนี้ไม่อยู่ในสถานะรออนุมัติ")
        return redirect("recruitment:requisition_detail", pk=pk)
    if not can_approve(request.user, requisition) and not (
        is_hr(request) or request.user.is_superuser
    ):
        return HttpResponseForbidden("ไม่มีสิทธิ์ปฏิเสธคำขอนี้")

    reject_requisition(requisition)
    messages.success(request, "ปฏิเสธคำขอแล้ว")
    return redirect("recruitment:requisition_detail", pk=pk)


@login_required
@require_POST
def requisition_hr_map(request, pk):
    if not (is_hr(request) or request.user.is_superuser):
        return HttpResponseForbidden("เฉพาะ HR")

    requisition = get_object_or_404(Requisition, pk=pk)
    form = HRMapForm(request.POST, requisition=requisition)
    if not form.is_valid():
        messages.error(request, "ข้อมูลผูกตำแหน่งไม่ถูกต้อง")
        return redirect("recruitment:requisition_detail", pk=pk)

    map_position_and_sync(
        requisition,
        position=form.cleaned_data["position"],
        approved_headcount=form.cleaned_data["approved_headcount"],
    )
    messages.success(request, "ผูกตำแหน่งและซิงก์โควตาแล้ว")
    return redirect("recruitment:requisition_detail", pk=pk)
