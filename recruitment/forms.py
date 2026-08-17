from django import forms

from .models import Candidate, Company, Department, Division, EmployeeLevel, JobApplication, JobPosition, Requisition, WorkLocation


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


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = (
            "title_name_th",
            "first_name_th",
            "last_name_th",
            "nickname",
            "phone_number",
            "phone_number1",
            "email",
            "idcard",
            "sex",
            "birthday",
            "profile_picture",
        )
        widgets = {
            "title_name_th": forms.TextInput(attrs={"class": "text-input"}),
            "first_name_th": forms.TextInput(attrs={"class": "text-input"}),
            "last_name_th": forms.TextInput(attrs={"class": "text-input"}),
            "nickname": forms.TextInput(attrs={"class": "text-input"}),
            "phone_number": forms.TextInput(attrs={"class": "text-input"}),
            "phone_number1": forms.TextInput(attrs={"class": "text-input"}),
            "email": forms.EmailInput(attrs={"class": "text-input"}),
            "idcard": forms.TextInput(attrs={"class": "text-input"}),
            "sex": forms.TextInput(attrs={"class": "text-input"}),
            "birthday": forms.DateInput(attrs={"class": "text-input", "type": "date"}),
            "profile_picture": forms.ClearableFileInput(attrs={"class": "text-input"}),
        }

    def clean_email(self):
        value = (self.cleaned_data.get("email") or "").strip()
        return value or None

    def clean_phone_number(self):
        return (self.cleaned_data.get("phone_number") or "").strip()
