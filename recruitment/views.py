from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from .address import lookup_zip
from .auth import can_decide_requisition, can_edit_requisition, can_hr_finalize, can_reject_requisition, can_view_requisition, is_designated_manager, require_hr, user_is_hr
from .forms import (
    AcquaintanceFormSet,
    CandidateForm,
    CompanyForm,
    DepartmentForm,
    DivisionForm,
    EmployeeLevelForm,
    GuarantorFormSet,
    HRMapForm,
    InterviewForm,
    JobApplicationEditForm,
    JobApplicationForm,
    JobPositionForm,
    RequisitionCreateForm,
    RequisitionDecideForm,
    RequisitionEditForm,
    StartWorkForm,
    StudyFormSet,
    WorkLocationForm,
    candidate_missing_profile_labels,
)
from .line import build_authorize_url, fetch_line_user_id, line_configured, new_state
from .mail import (
    create_interview_google_calendar,
    create_start_work_google_calendar,
    interview_end,
    send_candidate_interview_email,
)
from .models import Candidate, Company, Department, Division, EmployeeLevel, EmployeeRecord, JobApplication, JobPosition, Requisition, User, WorkLocation
from .services import approve_requisition, map_position_and_sync, reject_requisition


@login_required
def home(request):
    if user_is_hr(request.user):
        qs = Requisition.objects.all()
        awaiting_hr = (
            Requisition.objects.filter(status=Requisition.Status.MANAGER_APPROVED)
            .select_related("requester", "position")
            .order_by("-updated_at")[:10]
        )
        return render(
            request,
            "recruitment/hr/home_hr.html",
            {
                "count_pending": qs.filter(status=Requisition.Status.PENDING).count(),
                "count_manager_approved": qs.filter(
                    status=Requisition.Status.MANAGER_APPROVED
                ).count(),
                "count_hr_approved": qs.filter(
                    status=Requisition.Status.HR_APPROVED
                ).count(),
                "count_rejected": qs.filter(status=Requisition.Status.REJECTED).count(),
                "awaiting_hr": awaiting_hr,
            },
        )
    return render(request, "recruitment/home.html")


@login_required
def my_positions(request):
    """Read-only positions for picking a title into a requisition."""
    division_name = (request.user.division or "").strip()
    department_name = (request.user.department or "").strip()
    is_hr = user_is_hr(request.user)
    qs = JobPosition.objects.select_related("department", "department__division")
    if not is_hr:
        qs = JobPosition.objects.none()
        if division_name:
            qs = JobPosition.objects.select_related(
                "department", "department__division"
            ).filter(department__division__name__iexact=division_name)
            if department_name:
                qs = qs.filter(department__name__iexact=department_name)
    return render(
        request,
        "recruitment/my_positions.html",
        {
            "positions": qs,
            "division_name": division_name,
            "department_name": department_name,
            "show_all": is_hr,
        },
    )


@login_required
def requisition_list(request):
    """List of requisitions for the user."""
    if user_is_hr(request.user):
        qs = Requisition.objects.select_related("requester", "position")
    else:
        qs = Requisition.objects.filter(requester=request.user).select_related(
            "requester", "position"
        )
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()
    if q:
        qs = qs.filter(
            Q(position_title__icontains=q)
            | Q(requester__nickname__icontains=q)
            | Q(requester__person_unid__icontains=q)
            | Q(approver_unid__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    return render(
        request,
        "recruitment/requisition_list.html",
        {
            "requisitions": qs,
            "filter_q": q,
            "filter_status": status,
            "filter_priority": priority,
            "status_choices": Requisition.Status.choices,
            "priority_choices": Requisition.Priority.choices,
        },
    )


@login_required
def requisition_create(request):
    """Create a new requisition."""
    if request.method == "POST":
        form = RequisitionCreateForm(request.POST)

        if form.is_valid():
            requisition = form.save(commit=False)
            requisition.requester = request.user
            requisition.approver_unid = request.user.approve_code or ""
            requisition.status = Requisition.Status.PENDING
            requisition.save()
            if requisition.approver_unid:
                messages.success(request, "สร้างคำขออัตรากำลังแล้ว ส่งให้หัวหน้าอนุมัติ")
            else:
                messages.success(request, "สร้างคำขออัตรากำลังแล้ว")
            return redirect("recruitment:requisition_detail", pk=requisition.pk)
    else:
        form = RequisitionCreateForm(
            initial={
                "position_title": request.GET.get("title", "").strip(),
                "job_description": request.GET.get("description", "").strip(),
            }
        )

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
    """Edit a requisition."""
    requisition = get_object_or_404(Requisition, pk=pk)
    if not can_edit_requisition(request.user, requisition):
        return HttpResponseForbidden("ไม่มีสิทธิ์แก้ไขคำขอนี้")

    acting_as_hr = user_is_hr(request.user) and not is_designated_manager(
        request.user, requisition
    )
    if request.method == "POST":
        form = RequisitionEditForm(request.POST, instance=requisition)
        if form.is_valid():
            form.save()
            messages.success(request, "บันทึกการแก้ไขแล้ว")
            return redirect("recruitment:requisition_detail", pk=requisition.pk)
    else:
        form = RequisitionEditForm(instance=requisition)

    if acting_as_hr:
        page_copy = "HR กำลังแก้ไขแทนหัวหน้า — ปรับรายละเอียดและหมายเหตุได้ก่อนอนุมัติ"
    else:
        page_copy = "หัวหน้าสามารถปรับรายละเอียดและเขียนหมายเหตุได้ก่อนอนุมัติ"

    return render(
        request,
        "recruitment/requisition_form.html",
        {
            "form": form,
            "page_title": f"แก้ไขคำขอ #{requisition.pk}",
            "page_copy": page_copy,
            "submit_label": "บันทึก",
            "cancel_url": reverse(
                "recruitment:requisition_detail", kwargs={"pk": requisition.pk}
            ),
            "active_nav": "approvals",
        },
    )


@login_required
def requisition_detail(request, pk):
    """Detail of a requisition."""
    requisition = get_object_or_404(
        Requisition.objects.select_related("requester", "position"),
        pk=pk,
    )
    if not can_view_requisition(request, requisition):
        return HttpResponseForbidden("ไม่มีสิทธิ์ดูคำขอนี้")

    is_manager = is_designated_manager(request.user, requisition)
    is_hr_user = user_is_hr(request.user)
    can_decide = can_decide_requisition(request.user, requisition)
    acting_as_hr = can_decide and is_hr_user and not is_manager
    can_finalize = can_hr_finalize(request.user, requisition)

    decide_form = None
    hr_form = None
    if can_decide:
        decide_form = RequisitionDecideForm(requisition=requisition)
    if can_finalize:
        hr_form = HRMapForm(requisition=requisition)

    return render(
        request,
        "recruitment/requisition_detail.html",
        {
            "requisition": requisition,
            "decide_form": decide_form,
            "hr_form": hr_form,
            "can_decide": can_decide,
            "can_edit": can_edit_requisition(request.user, requisition),
            "is_hr_user": is_hr_user,
            "is_designated_manager": is_manager,
            "acting_as_hr": acting_as_hr,
        },
    )


@login_required
def approval_inbox(request):
    """List of requisitions for the user to approve."""
    is_hr_user = user_is_hr(request.user)
    if is_hr_user:
        statuses = [
            Requisition.Status.PENDING,
            Requisition.Status.MANAGER_APPROVED,
        ]
    else:
        statuses = [Requisition.Status.PENDING]
    qs = Requisition.objects.filter(status__in=statuses).select_related(
        "requester", "position"
    )
    scope = request.GET.get("scope", "all" if is_hr_user else "mine")
    if not is_hr_user or scope == "mine":
        qs = qs.filter(
            approver_unid=request.user.person_unid,
            status=Requisition.Status.PENDING,
        )
        scope = "mine"
    else:
        scope = "all"
    return render(
        request,
        "recruitment/approval_inbox.html",
        {
            "requisitions": qs.order_by("-created_at"),
            "approval_scope": scope,
            "is_hr_user": is_hr_user,
        },
    )


@login_required
@require_POST
def requisition_approve(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    if not can_decide_requisition(request.user, requisition):
        if requisition.status != Requisition.Status.PENDING:
            messages.error(request, "คำขอนี้ไม่อยู่ในสถานะรออนุมัติ")
            return redirect("recruitment:requisition_detail", pk=pk)
        return HttpResponseForbidden("ไม่มีสิทธิ์อนุมัติคำขอนี้")

    form = RequisitionDecideForm(request.POST, requisition=requisition)
    if not form.is_valid():
        messages.error(request, "ข้อมูลอนุมัติไม่ถูกต้อง")
        return redirect("recruitment:requisition_detail", pk=pk)

    approved_headcount = form.cleaned_data.get("approved_headcount") or requisition.required_headcount
    approve_requisition(requisition, approved_headcount=approved_headcount)
    if user_is_hr(request.user) and not is_designated_manager(request.user, requisition):
        messages.success(request, "หัวหน้าอนุมัติแล้ว (HR อนุมัติแทน)")
    else:
        messages.success(request, "หัวหน้าอนุมัติแล้ว ส่งต่อให้ฝ่ายบุคคล")
    return redirect("recruitment:requisition_detail", pk=pk)


@login_required
@require_POST
def requisition_reject(request, pk):
    requisition = get_object_or_404(Requisition, pk=pk)
    if not can_reject_requisition(request.user, requisition):
        if requisition.status not in (
            Requisition.Status.PENDING,
            Requisition.Status.MANAGER_APPROVED,
        ):
            messages.error(request, "คำขอนี้ไม่อยู่ในสถานะที่ปฏิเสธได้")
            return redirect("recruitment:requisition_detail", pk=pk)
        return HttpResponseForbidden("ไม่มีสิทธิ์ปฏิเสธคำขอนี้")

    reject_requisition(requisition)
    if user_is_hr(request.user) and not is_designated_manager(request.user, requisition):
        messages.success(request, "ปฏิเสธคำขอแล้ว (HR ดำเนินการแทนหัวหน้า)")
    else:
        messages.success(request, "ปฏิเสธคำขอแล้ว")
    return redirect("recruitment:requisition_detail", pk=pk)


@login_required
@require_POST
def requisition_hr_map(request, pk):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")

    requisition = get_object_or_404(Requisition, pk=pk)
    if not can_hr_finalize(request.user, requisition):
        messages.error(request, "คำขอนี้ยังไม่พร้อมให้ฝ่ายบุคคลอนุมัติ")
        return redirect("recruitment:requisition_detail", pk=pk)
    form = HRMapForm(request.POST, requisition=requisition)
    if not form.is_valid():
        messages.error(request, "ข้อมูลผูกตำแหน่งไม่ถูกต้อง")
        return redirect("recruitment:requisition_detail", pk=pk)

    map_position_and_sync(
        requisition,
        position=form.cleaned_data["position"],
        approved_headcount=form.cleaned_data["approved_headcount"],
    )
    messages.success(request, "ฝ่ายบุคคลอนุมัติแล้ว ผูกตำแหน่งและซิงก์โควตาแล้ว")
    return redirect("recruitment:requisition_detail", pk=pk)


# ---------------------------------------------------------------------------
# Master data: Division / Department / JobPosition (HR manage)
# ---------------------------------------------------------------------------

@login_required
def division_list(request):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    qs = Division.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(name__icontains=q)
    return render(
        request,
        "recruitment/hr/division_list.html",
        {
            "divisions": qs,
            "can_manage": True,
            "filter_q": q,
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
        "recruitment/hr/master_form.html",
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
        "recruitment/hr/master_form.html",
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
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    qs = Department.objects.select_related("division")
    q = request.GET.get("q", "").strip()
    division_id = request.GET.get("division", "").strip()
    if q:
        qs = qs.filter(name__icontains=q)
    if division_id.isdigit():
        qs = qs.filter(division_id=int(division_id))
    else:
        division_id = ""
    return render(
        request,
        "recruitment/hr/department_list.html",
        {
            "departments": qs,
            "can_manage": True,
            "filter_q": q,
            "filter_division": division_id,
            "divisions": Division.objects.all(),
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
        "recruitment/hr/master_form.html",
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
        "recruitment/hr/master_form.html",
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
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    qs = JobPosition.objects.select_related("department", "department__division")
    q = request.GET.get("q", "").strip()
    division_id = request.GET.get("division", "").strip()
    department_id = request.GET.get("department", "").strip()
    if q:
        qs = qs.filter(title__icontains=q)
    if division_id.isdigit():
        qs = qs.filter(department__division_id=int(division_id))
    else:
        division_id = ""
    departments = Department.objects.select_related("division")
    if division_id:
        departments = departments.filter(division_id=int(division_id))
    if department_id.isdigit():
        qs = qs.filter(department_id=int(department_id))
    else:
        department_id = ""
    return render(
        request,
        "recruitment/hr/position_list.html",
        {
            "positions": qs,
            "can_manage": True,
            "filter_q": q,
            "filter_division": division_id,
            "filter_department": department_id,
            "divisions": Division.objects.all(),
            "departments": departments,
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
        "recruitment/hr/master_form.html",
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
        "recruitment/hr/master_form.html",
        {
            "form": form,
            "page_title": f"แก้ไขตำแหน่ง {position.title}",
            "page_copy": f"{position.department.division} · {position.department}",
            "cancel_url": "recruitment:position_list",
            "active_nav": "positions",
        },
    )


def _hr_named_master_list(
    request,
    *,
    queryset,
    list_url,
    create_url,
    edit_url,
    page_title,
    page_copy,
    add_label,
    search_placeholder,
    active_nav,
):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    q = request.GET.get("q", "").strip()
    active = request.GET.get("active", "").strip()
    qs = queryset
    if q:
        qs = qs.filter(name__icontains=q)
    if active == "1":
        qs = qs.filter(is_active=True)
    elif active == "0":
        qs = qs.filter(is_active=False)
    else:
        active = ""
    return render(
        request,
        "recruitment/hr/named_master_list.html",
        {
            "items": qs,
            "can_manage": True,
            "filter_q": q,
            "filter_active": active,
            "list_url": list_url,
            "create_url": create_url,
            "edit_url": edit_url,
            "page_title": page_title,
            "page_copy": page_copy,
            "add_label": add_label,
            "search_placeholder": search_placeholder,
            "active_nav": active_nav,
        },
    )


def _hr_named_master_form(
    request,
    *,
    form_class,
    instance,
    list_url,
    page_title,
    page_copy,
    success_message,
    active_nav,
):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, success_message)
        return redirect(list_url)
    return render(
        request,
        "recruitment/hr/master_form.html",
        {
            "form": form,
            "page_title": page_title,
            "page_copy": page_copy,
            "cancel_url": list_url,
            "active_nav": active_nav,
        },
    )


@login_required
def company_list(request):
    return _hr_named_master_list(
        request,
        queryset=Company.objects.all().order_by("name"),
        list_url="recruitment:company_list",
        create_url="recruitment:company_create",
        edit_url="recruitment:company_edit",
        page_title="บริษัท",
        page_copy="Master Company — ใช้ตอนบันทึกประวัติพนักงาน",
        add_label="เพิ่มบริษัท",
        search_placeholder="ค้นหาชื่อบริษัท",
        active_nav="companies",
    )


@login_required
def company_create(request):
    return _hr_named_master_form(
        request,
        form_class=CompanyForm,
        instance=None,
        list_url="recruitment:company_list",
        page_title="เพิ่มบริษัท",
        page_copy="สร้างบริษัทใน master data",
        success_message="เพิ่มบริษัทแล้ว",
        active_nav="companies",
    )


@login_required
def company_edit(request, pk):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    company = get_object_or_404(Company, pk=pk)
    return _hr_named_master_form(
        request,
        form_class=CompanyForm,
        instance=company,
        list_url="recruitment:company_list",
        page_title=f"แก้ไขบริษัท {company.name}",
        page_copy="อัปเดตชื่อหรือสถานะใช้งาน",
        success_message="บันทึกบริษัทแล้ว",
        active_nav="companies",
    )


@login_required
def work_location_list(request):
    return _hr_named_master_list(
        request,
        queryset=WorkLocation.objects.all().order_by("name"),
        list_url="recruitment:work_location_list",
        create_url="recruitment:work_location_create",
        edit_url="recruitment:work_location_edit",
        page_title="สถานที่ทำงาน",
        page_copy="Master WorkLocation — สถานที่ปฏิบัติงาน",
        add_label="เพิ่มสถานที่",
        search_placeholder="ค้นหาสถานที่ทำงาน",
        active_nav="locations",
    )


@login_required
def work_location_create(request):
    return _hr_named_master_form(
        request,
        form_class=WorkLocationForm,
        instance=None,
        list_url="recruitment:work_location_list",
        page_title="เพิ่มสถานที่ทำงาน",
        page_copy="สร้างสถานที่ใน master data",
        success_message="เพิ่มสถานที่ทำงานแล้ว",
        active_nav="locations",
    )


@login_required
def work_location_edit(request, pk):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    location = get_object_or_404(WorkLocation, pk=pk)
    return _hr_named_master_form(
        request,
        form_class=WorkLocationForm,
        instance=location,
        list_url="recruitment:work_location_list",
        page_title=f"แก้ไขสถานที่ {location.name}",
        page_copy="อัปเดตชื่อหรือสถานะใช้งาน",
        success_message="บันทึกสถานที่ทำงานแล้ว",
        active_nav="locations",
    )


@login_required
def employee_level_list(request):
    return _hr_named_master_list(
        request,
        queryset=EmployeeLevel.objects.all().order_by("name"),
        list_url="recruitment:employee_level_list",
        create_url="recruitment:employee_level_create",
        edit_url="recruitment:employee_level_edit",
        page_title="ระดับพนักงาน",
        page_copy="Master EmployeeLevel — ระดับ/เกรดพนักงาน",
        add_label="เพิ่มระดับ",
        search_placeholder="ค้นหาระดับพนักงาน",
        active_nav="levels",
    )


@login_required
def employee_level_create(request):
    return _hr_named_master_form(
        request,
        form_class=EmployeeLevelForm,
        instance=None,
        list_url="recruitment:employee_level_list",
        page_title="เพิ่มระดับพนักงาน",
        page_copy="สร้างระดับใน master data",
        success_message="เพิ่มระดับพนักงานแล้ว",
        active_nav="levels",
    )


@login_required
def employee_level_edit(request, pk):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    level = get_object_or_404(EmployeeLevel, pk=pk)
    return _hr_named_master_form(
        request,
        form_class=EmployeeLevelForm,
        instance=level,
        list_url="recruitment:employee_level_list",
        page_title=f"แก้ไขระดับ {level.name}",
        page_copy="อัปเดตชื่อหรือสถานะใช้งาน",
        success_message="บันทึกระดับพนักงานแล้ว",
        active_nav="levels",
    )


@login_required
def line_connect(request):
    if not line_configured():
        messages.error(request, "ยังไม่ได้ตั้งค่า LINE Login ใน .env")
        return redirect("recruitment:home")
    state = new_state()
    request.session["line_oauth_state"] = state
    return redirect(build_authorize_url(state))


@login_required
@require_GET
def line_callback(request):
    if request.GET.get("error"):
        messages.error(request, "ยกเลิกการเชื่อม LINE หรือ LINE ปฏิเสธการเข้าถึง")
        return redirect("recruitment:home")
    state = request.GET.get("state", "")
    code = request.GET.get("code", "")
    expected = request.session.pop("line_oauth_state", "")
    if not code or not state or state != expected:
        messages.error(request, "การเชื่อม LINE ไม่ถูกต้อง (state)")
        return redirect("recruitment:home")
    try:
        line_user_id = fetch_line_user_id(code)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("recruitment:home")

    taken = (
        User.objects.filter(line_user_id=line_user_id)
        .exclude(pk=request.user.pk)
        .exists()
    )
    if taken:
        messages.error(request, "บัญชี LINE นี้ถูกผูกกับผู้ใช้อื่นแล้ว")
        return redirect("recruitment:home")

    try:
        request.user.line_user_id = line_user_id
        request.user.save(update_fields=["line_user_id"])
    except IntegrityError:
        messages.error(request, "บันทึก LINE userId ไม่สำเร็จ")
        return redirect("recruitment:home")

    messages.success(request, "เชื่อม LINE สำหรับแจ้งเตือนแล้ว")
    return redirect("recruitment:home")


@login_required
@require_POST
def line_disconnect(request):
    request.user.line_user_id = None
    request.user.save(update_fields=["line_user_id"])
    messages.success(request, "ยกเลิกการเชื่อม LINE แล้ว")
    return redirect("recruitment:home")


# ---------------------------------------------------------------------------
# Phase 2: candidate duplicate check (HR)
# ---------------------------------------------------------------------------

@login_required
def list_candidate(request):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    latest_status = (
        JobApplication.objects.filter(candidate_id=OuterRef("pk"))
        .order_by("-created_at")
        .values("status")[:1]
    )
    qs = Candidate.objects.annotate(
        application_count=Count("applications"),
        latest_status=Subquery(latest_status),
    )
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if q:
        qs = qs.filter(
            Q(first_name_th__icontains=q)
            | Q(last_name_th__icontains=q)
            | Q(nickname__icontains=q)
            | Q(phone_number__icontains=q)
            | Q(email__icontains=q)
            | Q(idcard__icontains=q)
        )
    if status:
        qs = qs.filter(latest_status=status)
    return render(
        request,
        "recruitment/hr/candidate_list.html",
        {
            "candidates": qs,
            "filter_q": q,
            "filter_status": status,
            "status_choices": JobApplication.Status.choices,
        },
    )


@login_required
def list_job_application(request):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    qs = JobApplication.objects.select_related(
        "candidate",
        "position",
        "position__department",
        "position__department__division",
    )
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    position_id = request.GET.get("position", "").strip()
    if q:
        qs = qs.filter(
            Q(candidate__first_name_th__icontains=q)
            | Q(candidate__last_name_th__icontains=q)
            | Q(candidate__nickname__icontains=q)
            | Q(candidate__phone_number__icontains=q)
            | Q(candidate__email__icontains=q)
            | Q(position__title__icontains=q)
            | Q(origin__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if position_id.isdigit():
        qs = qs.filter(position_id=int(position_id))
    else:
        position_id = ""
    return render(
        request,
        "recruitment/hr/job_application_list.html",
        {
            "applications": qs,
            "filter_q": q,
            "filter_status": status,
            "filter_position": position_id,
            "status_choices": JobApplication.Status.choices,
            "positions": JobPosition.objects.select_related(
                "department", "department__division"
            ),
        },
    )


@login_required
def job_application_detail(request, pk):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    application = get_object_or_404(
        JobApplication.objects.select_related(
            "candidate",
            "position",
            "position__department",
            "position__department__division",
            "hired_record",
            "hired_record__company",
            "hired_record__location",
            "hired_record__employee_level",
        ).prefetch_related(
            "candidate__acquaintances",
            "candidate__guarantors",
            "candidate__studies",
        ),
        pk=pk,
    )
    candidate = application.candidate
    interview_end_at = None
    if application.appointment_date:
        interview_end_at = interview_end(application.appointment_date)
    return render(
        request,
        "recruitment/hr/job_application_detail.html",
        {
            "application": application,
            "candidate": candidate,
            "interview_end_at": interview_end_at,
        },
    )


@login_required
def job_application_edit(request, pk):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    application = get_object_or_404(
        JobApplication.objects.select_related("candidate", "position"),
        pk=pk,
    )
    candidate = application.candidate
    if request.method == "POST":
        candidate_form = CandidateForm(
            request.POST, request.FILES, instance=candidate, prefix="candidate"
        )
        application_form = JobApplicationEditForm(
            request.POST, request.FILES, instance=application, prefix="app"
        )
        if candidate_form.is_valid() and application_form.is_valid():
            candidate_form.save()
            application_form.save()
            messages.success(request, "บันทึกข้อมูลใบสมัครแล้ว")
            return redirect("recruitment:job_application_detail", pk=application.pk)
    else:
        candidate_form = CandidateForm(instance=candidate, prefix="candidate")
        application_form = JobApplicationEditForm(instance=application, prefix="app")
    return render(
        request,
        "recruitment/hr/job_application_edit.html",
        {
            "application": application,
            "candidate": candidate,
            "candidate_form": candidate_form,
            "application_form": application_form,
        },
    )


@login_required
def schedule_interview(request, application_id):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    application = get_object_or_404(
        JobApplication.objects.select_related("candidate", "position"),
        pk=application_id,
    )
    if application.status not in (
        JobApplication.Status.APPLIED,
        JobApplication.Status.INTERVIEWING,
    ):
        messages.error(request, "แก้ไขนัดสัมภาษณ์ได้เฉพาะสถานะสมัครใหม่หรือนัดสัมภาษณ์")
        return redirect("recruitment:job_application_detail", pk=application.pk)

    if request.method == "POST":
        form = InterviewForm(request.POST, instance=application)
        if form.is_valid():
            scheduled = form.save(commit=False)
            scheduled.status = JobApplication.Status.INTERVIEWING
            scheduled.save()
            notes = ["บันทึกวันนัดหมายแล้ว"]
            if form.cleaned_data.get("add_google_calendar"):
                try:
                    sent_cal, cal_dest = create_interview_google_calendar(scheduled)
                    notes.append(f"Google Calendar: {cal_dest}" if sent_cal else cal_dest)
                except Exception as exc:
                    notes.append(f"สร้างนัดใน Google Calendar ไม่สำเร็จ ({exc})")
            if form.cleaned_data.get("send_candidate_email"):
                try:
                    sent, dest = send_candidate_interview_email(scheduled)
                    notes.append(f"เมลผู้สมัคร: {dest}" if sent else dest)
                except Exception as exc:
                    notes.append(f"ส่งเมลผู้สมัครไม่สำเร็จ ({exc})")
            messages.success(request, " · ".join(notes))
            return redirect("recruitment:job_application_detail", pk=application.pk)
    else:
        form = InterviewForm(instance=application)

    return render(
        request,
        "recruitment/hr/schedule_interview.html",
        {"form": form, "application": application},
    )


@login_required
def schedule_start_work(request, application_id):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    application = get_object_or_404(
        JobApplication.objects.select_related(
            "candidate", "position", "hired_record"
        ),
        pk=application_id,
    )
    if application.status not in (
        JobApplication.Status.INTERVIEWING,
        JobApplication.Status.OFFERED,
    ):
        messages.error(request, "นัดเริ่มงานได้เมื่อสถานะเป็นนัดสัมภาษณ์หรือเสนอจ้างงาน")
        return redirect("recruitment:job_application_detail", pk=application.pk)

    missing = candidate_missing_profile_labels(application.candidate)
    if missing:
        messages.error(
            request,
            "กรอกข้อมูลผู้สมัครให้ครบก่อนยืนยันนัดเริ่มงาน: " + ", ".join(missing),
        )
        return redirect("recruitment:candidate_edit", pk=application.candidate.pk)

    record = getattr(application, "hired_record", None)
    if record is None:
        record = EmployeeRecord.objects.filter(candidate=application.candidate).first()
    if record is None:
        record = EmployeeRecord(
            candidate=application.candidate,
            employee_code=f"TMP{application.pk:06d}",
        )

    if request.method == "POST":
        form = StartWorkForm(
            request.POST, instance=record, application=application
        )
        if form.is_valid():
            record = form.save(commit=False)
            record.candidate = application.candidate
            record.application = application
            if not record.employee_code:
                record.employee_code = f"TMP{application.pk:06d}"
            record.save()
            application.position = form.cleaned_data["position"]
            application.start_work_date = record.start_date
            application.status = JobApplication.Status.OFFERED
            application.save()
            notes = ["ยืนยันตำแหน่งและบันทึกนัดเริ่มงานแล้ว"]
            if form.cleaned_data.get("add_google_calendar"):
                try:
                    sent_cal, cal_dest = create_start_work_google_calendar(application)
                    notes.append(f"Google Calendar: {cal_dest}" if sent_cal else cal_dest)
                except Exception as exc:
                    notes.append(f"สร้างนัดใน Google Calendar ไม่สำเร็จ ({exc})")
            messages.success(request, " · ".join(notes))
            return redirect("recruitment:job_application_detail", pk=application.pk)
    else:
        form = StartWorkForm(instance=record, application=application)
    return render(
        request,
        "recruitment/hr/schedule_start_work.html",
        {"form": form, "application": application},
    )


@login_required
def check_candidate(request):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    if request.method != "POST":
        return render(request, "recruitment/hr/check_candidate.html")

    search_term = (request.POST.get("search_term") or "").strip()
    if not search_term:
        messages.error(request, "กรอกอีเมลหรือเบอร์โทรศัพท์")
        return render(request, "recruitment/hr/check_candidate.html")

    if "@" in search_term:
        candidate = Candidate.objects.filter(email=search_term).first()
        not_found_params = {"email": search_term}
    else:
        candidate = Candidate.objects.filter(phone_number=search_term).first()
        not_found_params = {"phone": search_term}

    if candidate:
        return redirect(
            "recruitment:create_application_for_existing",
            candidate_id=candidate.pk,
        )

    url = reverse("recruitment:create_new_candidate")
    return redirect(f"{url}?{urlencode(not_found_params)}")


@login_required
def create_application_for_existing(request, candidate_id):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    candidate = get_object_or_404(Candidate, id=candidate_id)
    past_applications = candidate.applications.select_related(
        "position", "position__department", "position__department__division"
    ).order_by("-created_at")

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.candidate = candidate
            application.save()
            messages.success(request, f"สร้างใบสมัครให้ {candidate} แล้ว")
            return redirect("recruitment:home")
    else:
        form = JobApplicationForm()

    return render(
        request,
        "recruitment/hr/existing_candidate.html",
        {
            "candidate": candidate,
            "past_applications": past_applications,
            "form": form,
        },
    )


@login_required
def lookup_thai_address(request):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    matches = lookup_zip(request.GET.get("zip", ""))
    return JsonResponse({"matches": matches})


@login_required
def candidate_edit(request, pk):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == "POST":
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        study_formset = StudyFormSet(request.POST, instance=candidate)
        guarantor_formset = GuarantorFormSet(request.POST, instance=candidate)
        acquaintance_formset = AcquaintanceFormSet(request.POST, instance=candidate)
        if (
            form.is_valid()
            and study_formset.is_valid()
            and guarantor_formset.is_valid()
            and acquaintance_formset.is_valid()
        ):
            form.save()
            study_formset.save()
            guarantor_formset.save()
            acquaintance_formset.save()
            messages.success(request, f"บันทึกข้อมูล {candidate} แล้ว")
            return redirect("recruitment:list_candidate")
    else:
        form = CandidateForm(instance=candidate)
        study_formset = StudyFormSet(instance=candidate)
        guarantor_formset = GuarantorFormSet(instance=candidate)
        acquaintance_formset = AcquaintanceFormSet(instance=candidate)
    return render(
        request,
        "recruitment/hr/candidate_edit.html",
        {
            "form": form,
            "candidate": candidate,
            "study_formset": study_formset,
            "guarantor_formset": guarantor_formset,
            "acquaintance_formset": acquaintance_formset,
        },
    )


@login_required
def create_new_candidate(request):
    if not require_hr(request):
        return HttpResponseForbidden("เฉพาะ HR")

    initial = {}
    phone = (request.GET.get("phone") or "").strip()
    email = (request.GET.get("email") or "").strip()
    if phone:
        initial["phone_number"] = phone
    if email:
        initial["email"] = email

    if request.method == "POST":
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save()
            messages.success(request, f"สร้างโปรไฟล์ {candidate} แล้ว")
            return redirect(
                "recruitment:create_application_for_existing",
                candidate_id=candidate.pk,
            )
    else:
        form = CandidateForm(initial=initial)

    return render(
        request,
        "recruitment/hr/create_new_candidate.html",
        {"form": form, "prefill_phone": phone, "prefill_email": email},
    )

