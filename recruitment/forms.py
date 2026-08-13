from django import forms

from .models import Department, Division, JobPosition, Requisition


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
            "position",
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
            "position": forms.Select(attrs={"class": "text-input"}),
        }
        labels = {
            "position_title": "ชื่อตำแหน่ง",
            "required_headcount": "จำนวนที่ขอ",
            "priority": "ความเร่งด่วน",
            "job_description": "ละเอียดงาน",
            "position": "ตำแหน่งงาน (ถ้าทราบ)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["position"].queryset = JobPosition.objects.select_related(
            "department", "department__division"
        )
        self.fields["position"].required = False
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
