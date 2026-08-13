from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .auth import (
    can_approve,
    can_edit_requisition,
    can_view_requisition,
    is_hr,
    require_hr,
)
from .forms import (
    DepartmentForm,
    DivisionForm,
    HRMapForm,
    JobPositionForm,
    RequisitionCreateForm,
    RequisitionDecideForm,
    RequisitionEditForm,
)
from .models import Department, Division, JobPosition, Requisition
from .services import approve_requisition, map_position_and_sync, reject_requisition


@login_required
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

    return render(
        request,
        "recruitment/requisition_form.html",
        {
            "form": form,
            "page_title": "สร้างคำขออัตรากำลัง",
            "page_copy": (
                f'จะส่งให้หัวหน้าอัตโนมัติ: <strong>{request.user.approve_code or "—"}</strong>'
                " (จาก approve_code)"
            ),
            "submit_label": "ส่งคำขอ",
            "cancel_url": reverse("recruitment:requisition_list"),
        },
    )


@login_required
def requisition_edit(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    if not can_edit_requisition(request.user, requisition):
        return HttpResponseForbidden("ไม่มีสิทธิ์แก้ไขคำขอนี้")

    if request.method == "POST":
        form = RequisitionEditForm(request.POST, instance=requisition)
        if form.is_valid():
            form.save()
            messages.success(request, "บันทึกการแก้ไขแล้ว")
            return redirect("recruitment:requisition_detail", pk=requisition.pk)
    else:
        form = RequisitionEditForm(instance=requisition)

    return render(
        request,
        "recruitment/requisition_form.html",
        {
            "form": form,
            "page_title": f"แก้ไขคำขอ #{requisition.pk}",
            "page_copy": "หัวหน้าสามารถปรับรายละเอียดและเขียนหมายเหตุได้ก่อนอนุมัติ",
            "submit_label": "บันทึก",
            "cancel_url": reverse(
                "recruitment:requisition_detail", kwargs={"pk": requisition.pk}
            ),
            "active_nav": "approvals",
        },
    )


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
            "can_edit": can_edit_requisition(request.user, requisition),
            "is_hr_user": is_hr(request) or request.user.is_superuser,
        },
    )


@login_required
def approval_inbox(request):
    qs = Requisition.objects.filter(status=Requisition.Status.PENDING).select_related(
        "requester", "position"
    )
    if not (is_hr(request) or request.user.is_superuser):
        qs = qs.filter(approver_unid=request.user.person_unid)
    return render(
        request,
        "recruitment/approval_inbox.html",
        {"requisitions": qs.order_by("-created_at")},
    )


@login_required
@require_POST
def requisition_approve(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    if requisition.status != Requisition.Status.PENDING:
        messages.error(request, "คำขอนี้ไม่อยู่ในสถานะรออนุมัติ")
        return redirect("recruitment:requisition_detail", pk=pk)
    if not can_approve(request.user, requisition):
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
    if not can_approve(request.user, requisition):
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


# ---------------------------------------------------------------------------
# Master data: Division / Department / JobPosition (HR manage)
# ---------------------------------------------------------------------------

@login_required
def division_list(request):
    return render(
        request,
        "recruitment/division_list.html",
        {
            "divisions": Division.objects.all(),
            "can_manage": require_hr(request),
        },
    )


@login_required
def division_create(request):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    form = DivisionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "เพิ่มฝ่ายแล้ว")
        return redirect("recruitment:division_list")
    return render(
        request,
        "recruitment/master_form.html",
        {
            "form": form,
            "page_title": "เพิ่มฝ่าย",
            "page_copy": "สร้างฝ่ายใหม่ใน master data",
            "cancel_url": "recruitment:division_list",
            "active_nav": "divisions",
        },
    )


@login_required
def division_edit(request, pk):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    division = get_object_or_404(Division, pk=pk)
    form = DivisionForm(request.POST or None, instance=division)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "บันทึกฝ่ายแล้ว")
        return redirect("recruitment:division_list")
    return render(
        request,
        "recruitment/master_form.html",
        {
            "form": form,
            "page_title": f"แก้ไขฝ่าย {division.name}",
            "page_copy": "อัปเดตชื่อฝ่าย",
            "cancel_url": "recruitment:division_list",
            "active_nav": "divisions",
        },
    )


@login_required
def department_list(request):
    return render(
        request,
        "recruitment/department_list.html",
        {
            "departments": Department.objects.select_related("division"),
            "can_manage": require_hr(request),
        },
    )


@login_required
def department_create(request):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    form = DepartmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "เพิ่มแผนกแล้ว")
        return redirect("recruitment:department_list")
    return render(
        request,
        "recruitment/master_form.html",
        {
            "form": form,
            "page_title": "เพิ่มแผนก",
            "page_copy": "เลือกฝ่าย (ระดับใหญ่กว่า) แล้วระบุชื่อแผนก",
            "cancel_url": "recruitment:department_list",
            "active_nav": "departments",
        },
    )


@login_required
def department_edit(request, pk):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    department = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=department)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "บันทึกแผนกแล้ว")
        return redirect("recruitment:department_list")
    return render(
        request,
        "recruitment/master_form.html",
        {
            "form": form,
            "page_title": f"แก้ไขแผนก {department.name}",
            "page_copy": f"ฝ่าย: {department.division}",
            "cancel_url": "recruitment:department_list",
            "active_nav": "departments",
        },
    )


@login_required
def position_list(request):
    return render(
        request,
        "recruitment/position_list.html",
        {
            "positions": JobPosition.objects.select_related(
                "department", "department__division"
            ),
            "can_manage": require_hr(request),
        },
    )


@login_required
def position_create(request):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    form = JobPositionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "เพิ่มตำแหน่งงานแล้ว")
        return redirect("recruitment:position_list")
    return render(
        request,
        "recruitment/master_form.html",
        {
            "form": form,
            "page_title": "เพิ่มตำแหน่งงาน",
            "page_copy": "ผูกตำแหน่งกับแผนก และตั้งโควตาเริ่มต้น",
            "cancel_url": "recruitment:position_list",
            "active_nav": "positions",
        },
    )


@login_required
def position_edit(request, pk):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    position = get_object_or_404(JobPosition, pk=pk)
    form = JobPositionForm(request.POST or None, instance=position)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "บันทึกตำแหน่งงานแล้ว")
        return redirect("recruitment:position_list")
    return render(
        request,
        "recruitment/master_form.html",
        {
            "form": form,
            "page_title": f"แก้ไขตำแหน่ง {position.title}",
            "page_copy": f"{position.department.division} · {position.department}",
            "cancel_url": "recruitment:position_list",
            "active_nav": "positions",
        },
    )
