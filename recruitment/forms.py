from django import forms

from .address import lookup_zip
from .models import (
    Acquaintance,
    Candidate,
    Company,
    ContractTemplate,
    ContractType,
    Department,
    Division,
    EmployeeLevel,
    EmployeeRecord,
    Guarantor,
    JobApplication,
    JobPosition,
    Requisition,
    Study,
    WorkLocation,
)

CANDIDATE_REQUIRED_FIELDS = (
    "title_name_th",
    "first_name_th",
    "last_name_th",
    "first_name",
    "last_name",
    "sex",
    "address",
    "zip",
    "tambon",
    "amphure",
    "province",
)
CANDIDATE_PRESENT_FIELDS = (
    "address_present",
    "zip_present",
    "tambon_present",
    "amphure_present",
    "province_present",
)
CANDIDATE_FIELD_LABELS = {
    "title_name_th": "คำนำหน้า",
    "first_name_th": "ชื่อ (ไทย)",
    "last_name_th": "นามสกุล (ไทย)",
    "title_name": "คำนำหน้า (อังกฤษ)",
    "first_name": "ชื่อ (อังกฤษ)",
    "last_name": "นามสกุล (อังกฤษ)",
    "sex": "เพศ",
    "address": "ที่อยู่ตามบัตรประชาชน",
    "zip": "รหัสไปรษณีย์",
    "tambon": "แขวง/ตำบล",
    "amphure": "เขต/อำเภอ",
    "province": "จังหวัด",
    "address_present": "ที่อยู่ปัจจุบัน",
    "zip_present": "รหัสไปรษณีย์ปัจจุบัน",
    "tambon_present": "แขวง/ตำบลปัจจุบัน",
    "amphure_present": "เขต/อำเภอปัจจุบัน",
    "province_present": "จังหวัดปัจจุบัน",
}


TITLE_TH_TO_EN = {
    "นาย": "Mr.",
    "นาง": "Mrs.",
    "นางสาว": "Miss",
}
TITLE_TH_CHOICES = [
    ("", "เลือกคำนำหน้า"),
    ("นาย", "นาย"),
    ("นาง", "นาง"),
    ("นางสาว", "นางสาว"),
]


def candidate_missing_profile_labels(candidate):
    missing = []
    for name in CANDIDATE_REQUIRED_FIELDS:
        if not str(getattr(candidate, name, "") or "").strip():
            missing.append(CANDIDATE_FIELD_LABELS[name])
    present_filled = all(
        str(getattr(candidate, name, "") or "").strip()
        for name in CANDIDATE_PRESENT_FIELDS
    )
    if not present_filled:
        missing.extend(CANDIDATE_FIELD_LABELS[name] for name in CANDIDATE_PRESENT_FIELDS)
    return missing


class AnyTambonField(forms.ChoiceField):
    def valid_value(self, value):
        return True


class TambonSelect(forms.Select):
    def __init__(self, attrs=None, choices=(), extra=None):
        self.extra = extra or {}
        super().__init__(attrs, choices)

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        meta = self.extra.get(str(value or ""), {})
        if meta:
            option["attrs"]["data-amphure"] = meta.get("amphure") or ""
            option["attrs"]["data-province"] = meta.get("province") or ""
        return option


def _posted_or_instance(form, name):
    if form.is_bound:
        return form.data.get(form.add_prefix(name)) or ""
    return form.initial.get(name) or getattr(form.instance, name, "") or ""


def tambon_choice_data(zip_code, selected=""):
    choices = [("", "เลือกหลังกรอกรหัสไปรษณีย์")]
    extra = {}
    try:
        rows = lookup_zip(zip_code)
    except Exception:
        rows = []
    seen = {""}
    for row in rows:
        name = (row.get("tambon") or "").strip()
        if not name or name in seen:
            continue
        choices.append((name, name))
        extra[name] = row
        seen.add(name)
    selected = (selected or "").strip()
    if selected and selected not in seen:
        choices.append((selected, selected))
    return choices, extra


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ("name", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"class": "text-input"}),
        }
        labels = {"name": "ชื่อบริษัท", "is_active": "เปิดใช้งาน"}


class WorkLocationForm(forms.ModelForm):
    class Meta:
        model = WorkLocation
        fields = ("name", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"class": "text-input"}),
        }
        labels = {"name": "สถานที่ทำงาน", "is_active": "เปิดใช้งาน"}


class EmployeeLevelForm(forms.ModelForm):
    class Meta:
        model = EmployeeLevel
        fields = ("name", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"class": "text-input"}),
        }
        labels = {"name": "ระดับพนักงาน", "is_active": "เปิดใช้งาน"}


class ContractTypeForm(forms.ModelForm):
    class Meta:
        model = ContractType
        fields = ("name", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"class": "text-input"}),
        }
        labels = {"name": "ประเภทสัญญา", "is_active": "เปิดใช้งาน"}


class DivisionForm(forms.ModelForm):
    class Meta:
        model = Division
        fields = ("name",)
        widgets = {
            "name": forms.TextInput(attrs={"class": "text-input"}),
        }
        labels = {
            "name": "ชื่อฝ่าย",
        }


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("division", "name")
        widgets = {
            "division": forms.Select(attrs={"class": "text-input"}),
            "name": forms.TextInput(attrs={"class": "text-input"}),
        }
        labels = {
            "division": "ฝ่าย",
            "name": "ชื่อแผนก",
        }


class JobPositionForm(forms.ModelForm):
    class Meta:
        model = JobPosition
        fields = (
            "department",
            "title",
            "description",
            "current_headcount",
            "target_headcount",
        )
        widgets = {
            "department": forms.Select(attrs={"class": "text-input"}),
            "title": forms.TextInput(attrs={"class": "text-input"}),
            "description": forms.Textarea(attrs={"class": "text-input", "rows": 4}),
            "current_headcount": forms.NumberInput(
                attrs={"min": 0, "class": "text-input"}
            ),
            "target_headcount": forms.NumberInput(
                attrs={"min": 0, "class": "text-input"}
            ),
        }
        labels = {
            "department": "แผนก",
            "title": "ชื่อตำแหน่ง",
            "description": "รายละเอียด",
            "current_headcount": "จำนวนคนปัจจุบัน",
            "target_headcount": "โควตาเปิดรับ",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = Department.objects.select_related(
            "division"
        )


class RequisitionCreateForm(forms.ModelForm):
    class Meta:
        model = Requisition
        fields = (
            "position_title",
            "required_headcount",
            "priority",
            "job_description",
        )
        widgets = {
            "position_title": forms.TextInput(attrs={"class": "text-input"}),
            "required_headcount": forms.NumberInput(
                attrs={"min": 1, "class": "text-input"}
            ),
            "priority": forms.Select(attrs={"class": "text-input"}),
            "job_description": forms.Textarea(
                attrs={"class": "text-input", "rows": 5}
            ),
        }
        labels = {
            "position_title": "ชื่อตำแหน่ง",
            "required_headcount": "จำนวนที่ขอ",
            "priority": "ความเร่งด่วน",
            "job_description": "ละเอียดงาน",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["job_description"].required = False
        self.fields["position_title"].required = True

    def clean_required_headcount(self):
        value = self.cleaned_data["required_headcount"]
        if value < 1:
            raise forms.ValidationError("ต้องขออย่างน้อย 1 อัตรา")
        return value

    def clean_position_title(self):
        value = (self.cleaned_data.get("position_title") or "").strip()
        if not value:
            raise forms.ValidationError("กรุณาระบุชื่อตำแหน่ง")
        return value


class RequisitionEditForm(forms.ModelForm):
    class Meta:
        model = Requisition
        fields = (
            "position_title",
            "required_headcount",
            "priority",
            "job_description",
            "approver_note",
        )
        widgets = {
            "position_title": forms.TextInput(attrs={"class": "text-input"}),
            "required_headcount": forms.NumberInput(
                attrs={"min": 1, "class": "text-input"}
            ),
            "priority": forms.Select(attrs={"class": "text-input"}),
            "job_description": forms.Textarea(
                attrs={"class": "text-input", "rows": 5}
            ),
            "approver_note": forms.Textarea(attrs={"class": "text-input", "rows": 4}),
        }
        labels = {
            "position_title": "ชื่อตำแหน่ง",
            "required_headcount": "จำนวนที่ขอ",
            "priority": "ความเร่งด่วน",
            "job_description": "ละเอียดงาน",
            "approver_note": "หมายเหตุ (หัวหน้า)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["job_description"].required = False
        self.fields["approver_note"].required = False
        self.fields["position_title"].required = True

    def clean_required_headcount(self):
        value = self.cleaned_data["required_headcount"]
        if value < 1:
            raise forms.ValidationError("ต้องขออย่างน้อย 1 อัตรา")
        return value

    def clean_position_title(self):
        value = (self.cleaned_data.get("position_title") or "").strip()
        if not value:
            raise forms.ValidationError("กรุณาระบุชื่อตำแหน่ง")
        return value


class RequisitionDecideForm(forms.Form):
    approved_headcount = forms.IntegerField(
        min_value=1,
        required=False,
        label="จำนวนที่อนุมัติ",
        widget=forms.NumberInput(attrs={"min": 1, "class": "text-input"}),
    )

    def __init__(self, *args, requisition=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.requisition = requisition
        if requisition and not self.is_bound:
            self.fields["approved_headcount"].initial = requisition.required_headcount


class HRMapForm(forms.Form):
    position = forms.ModelChoiceField(
        queryset=JobPosition.objects.none(),
        label="ตำแหน่งงานอย่างเป็นทางการ",
        widget=forms.Select(attrs={"class": "text-input"}),
    )
    approved_headcount = forms.IntegerField(
        min_value=1,
        label="จำนวนที่อนุมัติ",
        widget=forms.NumberInput(attrs={"min": 1, "class": "text-input"}),
    )

    def __init__(self, *args, requisition=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["position"].queryset = JobPosition.objects.select_related(
            "department", "department__division"
        )
        if requisition and not self.is_bound:
            self.fields["approved_headcount"].initial = (
                requisition.approved_headcount or requisition.required_headcount
            )
            if requisition.position_id:
                self.fields["position"].initial = requisition.position_id


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ("position", "origin", "resume", "portfolio", "hr_note")
        widgets = {
            "position": forms.Select(attrs={"class": "text-input"}),
            "origin": forms.TextInput(
                attrs={"class": "text-input", "placeholder": "เช่น JobThai, Walk-in"}
            ),
            "resume": forms.ClearableFileInput(attrs={"class": "text-input"}),
            "portfolio": forms.ClearableFileInput(attrs={"class": "text-input"}),
            "hr_note": forms.Textarea(attrs={"class": "text-input", "rows": 4}),
        }
        labels = {
            "position": "ตำแหน่งที่สมัคร",
            "origin": "แหล่งที่มา",
            "resume": "ไฟล์ Resume",
            "portfolio": "ไฟล์ Portfolio",
            "hr_note": "บันทึกจาก HR",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["position"].queryset = JobPosition.objects.select_related(
            "department", "department__division"
        )
        self.fields["position"].label_from_instance = self._position_label
        self.fields["origin"].required = False
        self.fields["resume"].required = False
        self.fields["portfolio"].required = False
        self.fields["hr_note"].required = False

    @staticmethod
    def _position_label(obj):
        dept = obj.department
        division = dept.division.name if dept and dept.division_id else ""
        dept_name = dept.name if dept else ""
        org = " / ".join(part for part in (division, dept_name) if part)
        return f"{obj.title} ({org})" if org else obj.title


class JobApplicationEditForm(JobApplicationForm):
    class Meta(JobApplicationForm.Meta):
        fields = (
            "position",
            "origin",
            "status",
            "resume",
            "portfolio",
            "hr_note",
        )
        widgets = {
            **JobApplicationForm.Meta.widgets,
            "status": forms.Select(attrs={"class": "text-input"}),
        }
        labels = {
            **JobApplicationForm.Meta.labels,
            "status": "สถานะใบสมัคร",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].required = True


class InterviewForm(forms.ModelForm):
    send_candidate_email = forms.BooleanField(
        required=False,
        initial=True,
        label="ส่งเมลหาผู้สมัคร (Candidate)",
    )
    add_google_calendar = forms.BooleanField(
        required=False,
        initial=True,
        label="เพิ่มนัดใน Google Calendar",
    )

    class Meta:
        model = JobApplication
        fields = (
            "appointment_date",
            "interviewer_names",
            "interviewer_email",
            "ccmail",
            "is_online",
            "meeting_link",
        )
        widgets = {
            "appointment_date": forms.DateTimeInput(
                attrs={
                    "class": "text-input form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "interviewer_names": forms.TextInput(attrs={"class": "text-input form-control"}),
            "interviewer_email": forms.EmailInput(attrs={"class": "text-input form-control"}),
            "ccmail": forms.TextInput(
                attrs={
                    "class": "text-input form-control",
                    "placeholder": "head@company.com, other@company.com",
                }
            ),
            "meeting_link": forms.URLInput(attrs={"class": "text-input form-control"}),
        }
        labels = {
            "appointment_date": "วันและเวลาเริ่มนัดหมาย",
            "interviewer_names": "ผู้สัมภาษณ์",
            "interviewer_email": "อีเมลผู้สัมภาษณ์หลัก",
            "ccmail": "อีเมลผู้สัมภาษณ์เพิ่มเติม",
            "is_online": "สัมภาษณ์ออนไลน์",
            "meeting_link": "ลิงก์ประชุม",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["appointment_date"].required = True
        self.fields["appointment_date"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]
        self.fields["interviewer_names"].required = True
        self.fields["interviewer_email"].required = True
        self.fields["ccmail"].required = False
        self.fields["ccmail"].help_text = "คั่นด้วยจุลภาคเมื่อมีผู้สัมภาษณ์มากกว่า 1 คน"
        self.fields["meeting_link"].required = False
        self.order_fields(
            [
                "appointment_date",
                "interviewer_names",
                "interviewer_email",
                "ccmail",
                "is_online",
                "meeting_link",
                "send_candidate_email",
                "add_google_calendar",
            ]
        )


class StartWorkForm(forms.ModelForm):
    position = forms.ModelChoiceField(
        queryset=JobPosition.objects.select_related(
            "department", "department__division"
        ),
        label="ยืนยันตำแหน่ง",
        widget=forms.Select(attrs={"class": "text-input form-control"}),
    )
    add_google_calendar = forms.BooleanField(
        required=False,
        initial=True,
        label="เพิ่มนัดใน Google Calendar",
    )
    issue_contract = forms.BooleanField(
        required=False,
        initial=True,
        label="ออกหนังสือตามสัญญา (ดาวน์โหลดไฟล์ Word)",
    )

    class Meta:
        model = EmployeeRecord
        fields = ("start_date", "company", "location", "employee_level", "contract_type")
        widgets = {
            "start_date": forms.DateInput(
                attrs={"class": "text-input form-control", "type": "date"}
            ),
            "company": forms.Select(attrs={"class": "text-input form-control"}),
            "location": forms.Select(attrs={"class": "text-input form-control"}),
            "employee_level": forms.Select(attrs={"class": "text-input form-control"}),
            "contract_type": forms.Select(attrs={"class": "text-input form-control"}),
        }
        labels = {
            "start_date": "วันที่เริ่มงาน",
            "company": "บริษัท",
            "location": "สถานที่ทำงาน",
            "employee_level": "ระดับพนักงาน",
            "contract_type": "ประเภทสัญญา",
        }

    def __init__(self, *args, **kwargs):
        application = kwargs.pop("application", None)
        super().__init__(*args, **kwargs)
        self.fields["start_date"].required = True
        self.fields["company"].required = True
        self.fields["company"].queryset = Company.objects.filter(is_active=True)
        self.fields["location"].required = True
        self.fields["location"].queryset = WorkLocation.objects.filter(is_active=True)
        self.fields["employee_level"].required = True
        self.fields["employee_level"].queryset = EmployeeLevel.objects.filter(
            is_active=True
        )
        self.fields["contract_type"].required = True
        type_ids = list(
            ContractType.objects.filter(is_active=True).values_list("pk", flat=True)
        )
        current_type_id = getattr(self.instance, "contract_type_id", None)
        if current_type_id and current_type_id not in type_ids:
            type_ids.append(current_type_id)
        self.fields["contract_type"].queryset = ContractType.objects.filter(
            pk__in=type_ids
        )
        if application and not self.is_bound:
            self.fields["position"].initial = application.position_id
            if application.start_work_date and not getattr(self.instance, "start_date", None):
                self.fields["start_date"].initial = application.start_work_date
        self.fields["position"].label_from_instance = (
            lambda p: f"{p.title} — {p.department.division} / {p.department}"
            if getattr(p, "department_id", None)
            else p.title
        )
        self.order_fields(
            [
                "position",
                "start_date",
                "company",
                "location",
                "employee_level",
                "contract_type",
                "issue_contract",
                "add_google_calendar",
            ]
        )


class ContractTemplateForm(forms.ModelForm):
    class Meta:
        model = ContractTemplate
        fields = ("contract_type", "name", "file", "is_active")
        widgets = {
            "contract_type": forms.Select(attrs={"class": "text-input"}),
            "name": forms.TextInput(attrs={"class": "text-input"}),
            "file": forms.ClearableFileInput(attrs={"class": "text-input"}),
        }
        labels = {
            "contract_type": "ประเภทสัญญา",
            "name": "ชื่อเอกสาร",
            "file": "ไฟล์แม่แบบ (.docx)",
            "is_active": "เปิดใช้งาน",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        type_ids = list(
            ContractType.objects.filter(is_active=True).values_list("pk", flat=True)
        )
        current_type_id = getattr(self.instance, "contract_type_id", None)
        if current_type_id and current_type_id not in type_ids:
            type_ids.append(current_type_id)
        self.fields["contract_type"].queryset = ContractType.objects.filter(
            pk__in=type_ids
        )
        if self.instance.pk:
            self.fields["file"].required = False

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        if uploaded and not str(uploaded.name).lower().endswith(".docx"):
            raise forms.ValidationError("อัปโหลดได้เฉพาะไฟล์ .docx")
        return uploaded


class CandidateForm(forms.ModelForm):
    same_as_id_address = forms.BooleanField(
        required=False,
        initial=True,
        label="ที่อยู่ปัจจุบันเหมือนที่อยู่ตามบัตรประชาชน",
    )

    class Meta:
        model = Candidate
        fields = (
            "title_name_th",
            "first_name_th",
            "last_name_th",
            "first_name",
            "last_name",
            "nickname",
            "phone_number",
            "phone_number1",
            "email",
            "idcard",
            "sex",
            "birthday",
            "profile_picture",
            "address",
            "zip",
            "tambon",
            "amphure",
            "province",
            "address_present",
            "zip_present",
            "tambon_present",
            "amphure_present",
            "province_present",
        )
        widgets = {
            "title_name_th": forms.Select(attrs={"class": "text-input"}),
            "first_name_th": forms.TextInput(attrs={"class": "text-input"}),
            "last_name_th": forms.TextInput(attrs={"class": "text-input"}),
            "first_name": forms.TextInput(attrs={"class": "text-input"}),
            "last_name": forms.TextInput(attrs={"class": "text-input"}),
            "nickname": forms.TextInput(attrs={"class": "text-input"}),
            "phone_number": forms.TextInput(attrs={"class": "text-input"}),
            "phone_number1": forms.TextInput(attrs={"class": "text-input"}),
            "email": forms.EmailInput(attrs={"class": "text-input"}),
            "idcard": forms.TextInput(attrs={"class": "text-input"}),
            "sex": forms.Select(attrs={"class": "text-input"}),
            "birthday": forms.DateInput(attrs={"class": "text-input", "type": "date"}),
            "profile_picture": forms.ClearableFileInput(attrs={"class": "text-input"}),
            "address": forms.Textarea(
                attrs={"class": "text-input js-house", "rows": 2, "data-group": "id"}
            ),
            "zip": forms.TextInput(
                attrs={
                    "class": "text-input js-zip",
                    "maxlength": "5",
                    "inputmode": "numeric",
                    "placeholder": "เช่น 10160",
                    "data-group": "id",
                }
            ),
            "tambon": forms.Select(attrs={"class": "text-input js-tambon", "data-group": "id"}),
            "amphure": forms.TextInput(
                attrs={"class": "text-input js-amphure", "data-group": "id", "readonly": True}
            ),
            "province": forms.TextInput(
                attrs={"class": "text-input js-province", "data-group": "id", "readonly": True}
            ),
            "address_present": forms.Textarea(
                attrs={"class": "text-input js-house", "rows": 2, "data-group": "present"}
            ),
            "zip_present": forms.TextInput(
                attrs={
                    "class": "text-input js-zip",
                    "maxlength": "5",
                    "inputmode": "numeric",
                    "placeholder": "เช่น 10160",
                    "data-group": "present",
                }
            ),
            "tambon_present": forms.Select(
                attrs={"class": "text-input js-tambon", "data-group": "present"}
            ),
            "amphure_present": forms.TextInput(
                attrs={
                    "class": "text-input js-amphure",
                    "data-group": "present",
                    "readonly": True,
                }
            ),
            "province_present": forms.TextInput(
                attrs={
                    "class": "text-input js-province",
                    "data-group": "present",
                    "readonly": True,
                }
            ),
        }
        labels = {**CANDIDATE_FIELD_LABELS}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tambon_widget = {
            "class": "text-input js-tambon",
            "data-group": "id",
        }
        tambon_present_widget = {
            "class": "text-input js-tambon",
            "data-group": "present",
        }
        id_choices, id_extra = tambon_choice_data(
            _posted_or_instance(self, "zip"),
            _posted_or_instance(self, "tambon"),
        )
        present_choices, present_extra = tambon_choice_data(
            _posted_or_instance(self, "zip_present"),
            _posted_or_instance(self, "tambon_present"),
        )
        self.fields["tambon"] = AnyTambonField(
            choices=id_choices,
            required=False,
            widget=TambonSelect(attrs=tambon_widget, extra=id_extra),
            label=CANDIDATE_FIELD_LABELS["tambon"],
        )
        self.fields["tambon_present"] = AnyTambonField(
            choices=present_choices,
            required=False,
            widget=TambonSelect(attrs=tambon_present_widget, extra=present_extra),
            label=CANDIDATE_FIELD_LABELS["tambon_present"],
        )
        self.fields["title_name_th"] = forms.ChoiceField(
            choices=TITLE_TH_CHOICES,
            required=False,
            widget=forms.Select(attrs={"class": "text-input"}),
            label="คำนำหน้า",
        )
        current_title = ""
        if self.is_bound:
            current_title = self.data.get(self.add_prefix("title_name_th")) or ""
        if not current_title:
            current_title = (
                self.initial.get("title_name_th")
                or getattr(self.instance, "title_name_th", "")
                or ""
            )
        if current_title and current_title not in dict(TITLE_TH_CHOICES):
            self.fields["title_name_th"].choices = TITLE_TH_CHOICES + [
                (current_title, current_title)
            ]
        self.fields["sex"] = forms.ChoiceField(
            choices=[("", "เลือกเพศ"), ("ชาย", "ชาย"), ("หญิง", "หญิง")],
            required=False,
            widget=forms.Select(attrs={"class": "text-input"}),
            label="เพศ",
        )
        for name in CANDIDATE_REQUIRED_FIELDS + CANDIDATE_PRESENT_FIELDS:
            self.fields[name].required = False
        if self.instance and self.instance.pk:
            same = (
                (self.instance.address_present or "") == (self.instance.address or "")
                and (self.instance.zip_present or "") == (self.instance.zip or "")
                and (self.instance.tambon_present or "") == (self.instance.tambon or "")
            )
            self.fields["same_as_id_address"].initial = same or not (
                self.instance.address_present or self.instance.zip_present
            )
        self.order_fields(
            [
                "title_name_th",
                "first_name_th",
                "last_name_th",
                "first_name",
                "last_name",
                "nickname",
                "phone_number",
                "phone_number1",
                "email",
                "idcard",
                "sex",
                "birthday",
                "profile_picture",
                "address",
                "zip",
                "tambon",
                "amphure",
                "province",
                "same_as_id_address",
                "address_present",
                "zip_present",
                "tambon_present",
                "amphure_present",
                "province_present",
            ]
        )

    def clean(self):
        data = super().clean()
        data["title_name"] = TITLE_TH_TO_EN.get(data.get("title_name_th") or "", "")
        if data.get("same_as_id_address"):
            data["address_present"] = data.get("address")
            data["zip_present"] = data.get("zip")
            data["tambon_present"] = data.get("tambon")
            data["amphure_present"] = data.get("amphure")
            data["province_present"] = data.get("province")
        return data

    def save(self, commit=True):
        candidate = super().save(commit=False)
        candidate.title_name = self.cleaned_data.get("title_name") or None
        if commit:
            candidate.save()
        return candidate

    def clean_email(self):
        value = (self.cleaned_data.get("email") or "").strip()
        return value or None

    def clean_phone_number(self):
        return (self.cleaned_data.get("phone_number") or "").strip()


class StudyForm(forms.ModelForm):
    class Meta:
        model = Study
        fields = ("education", "institution", "major", "graduation", "grade", "country")
        widgets = {
            "education": forms.Select(attrs={"class": "text-input"}),
            "institution": forms.TextInput(attrs={"class": "text-input"}),
            "major": forms.TextInput(attrs={"class": "text-input"}),
            "graduation": forms.NumberInput(attrs={"class": "text-input"}),
            "grade": forms.NumberInput(attrs={"class": "text-input", "step": "0.01"}),
            "country": forms.Select(attrs={"class": "text-input"}),
        }
        labels = {
            "education": "ระดับการศึกษา",
            "institution": "สถาบันที่จบ",
            "major": "สาขาที่จบ",
            "graduation": "ปีที่จบ",
            "grade": "เกรดเฉลี่ย (GPA)",
            "country": "จบในประเทศไหน",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["education"].required = True
        self.fields["institution"].required = True
        self.fields["education"].choices = [("", "เลือกระดับ")] + list(
            Study.EDUCATION_CHOICES
        )
        self.fields["country"].required = False
        self.fields["country"].choices = [("", "ไม่ระบุ")] + list(Study.COUNTRY_CHOICES)


class GuarantorForm(forms.ModelForm):
    class Meta:
        model = Guarantor
        fields = ("name", "phone_number", "relation", "address")
        widgets = {
            "name": forms.TextInput(attrs={"class": "text-input"}),
            "phone_number": forms.TextInput(attrs={"class": "text-input"}),
            "relation": forms.Select(attrs={"class": "text-input"}),
            "address": forms.Textarea(attrs={"class": "text-input", "rows": 2}),
        }
        labels = {
            "name": "ชื่อ-นามสกุล",
            "phone_number": "เบอร์โทรศัพท์",
            "relation": "ความสัมพันธ์",
            "address": "ที่อยู่ติดต่อ",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["phone_number"].required = True
        self.fields["relation"].required = False
        self.fields["relation"].choices = [("", "ไม่ระบุ")] + [
            (k, v) for k, v in self.fields["relation"].choices if k != ""
        ]


class AcquaintanceForm(forms.ModelForm):
    class Meta:
        model = Acquaintance
        fields = ("name", "phone_number", "relation")
        widgets = {
            "name": forms.TextInput(attrs={"class": "text-input"}),
            "phone_number": forms.TextInput(attrs={"class": "text-input"}),
            "relation": forms.Select(attrs={"class": "text-input"}),
        }
        labels = {
            "name": "ชื่อ-นามสกุล",
            "phone_number": "เบอร์โทรศัพท์",
            "relation": "ความสัมพันธ์",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["phone_number"].required = True
        self.fields["relation"].required = False
        self.fields["relation"].choices = [("", "ไม่ระบุ")] + [
            (k, v) for k, v in self.fields["relation"].choices if k != ""
        ]
