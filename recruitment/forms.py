from django import forms

from .models import JobPosition, Requisition


class RequisitionCreateForm(forms.ModelForm):
    class Meta:
        model = Requisition
        fields = ("required_headcount", "priority", "required_date", "position")
        widgets = {
            "required_headcount": forms.NumberInput(attrs={"min": 1, "class": "text-input"}),
            "priority": forms.Select(attrs={"class": "text-input"}),
            "required_date": forms.DateInput(attrs={"type": "date", "class": "text-input"}),
            "position": forms.Select(attrs={"class": "text-input"}),
        }
        labels = {
            "required_headcount": "จำนวนที่ขอ",
            "priority": "ความเร่งด่วน",
            "required_date": "วันที่ต้องการ",
            "position": "ตำแหน่งงาน (ถ้าทราบ)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["position"].queryset = JobPosition.objects.select_related(
            "department", "department__division"
        )
        self.fields["position"].required = False
        self.fields["required_date"].required = False

    def clean_required_headcount(self):
        value = self.cleaned_data["required_headcount"]
        if value < 1:
            raise forms.ValidationError("ต้องขออย่างน้อย 1 อัตรา")
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
