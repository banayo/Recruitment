from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    Acquaintance,
    Candidate,
    Company,
    Department,
    Division,
    ContractTemplate,
    ContractType,
    EmployeeLevel,
    EmployeeRecord,
    Guarantor,
    JobApplication,
    JobPosition,
    Requisition,
    Study,
    User,
    WorkLocation,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "person_unid",
        "nickname",
        "role",
        "company_code",
        "division",
        "department",
        "line_user_id",
    )
    list_filter = ("role", "is_staff")
    search_fields = ("username", "person_unid", "nickname", "authentik_sub", "email", "line_user_id")
    ordering = ("person_unid",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "SSO / Profile",
            {
                "fields": (
                    "authentik_sub",
                    "person_unid",
                    "approve_code",
                    "role",
                    "gender",
                    "division",
                    "department",
                    "location",
                    "nickname",
                    "company_code",
                    "line_user_id",
                )
            },
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "SSO / Profile",
            {
                "fields": (
                    "authentik_sub",
                    "person_unid",
                    "approve_code",
                    "role",
                    "nickname",
                    "company_code",
                    "line_user_id",
                )
            },
        ),
    )


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "division")
    list_filter = ("division",)
    search_fields = ("name",)


@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "department",
        "current_headcount",
        "target_headcount",
    )
    list_filter = ("department",)
    search_fields = ("title",)


@admin.register(Requisition)
class RequisitionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "requester",
        "approver_unid",
        "position",
        "required_headcount",
        "approved_headcount",
        "status",
        "priority",
        "is_headcount_synced",
        "created_at",
    )
    list_filter = ("status", "priority", "is_headcount_synced")
    search_fields = ("approver_unid", "requester__person_unid", "requester__username")
    raw_id_fields = ("requester", "position")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)


@admin.register(WorkLocation)
class WorkLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)


@admin.register(EmployeeLevel)
class EmployeeLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)


@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("first_name_th", "last_name_th", "phone_number", "idcard", "created_at")
    search_fields = ("first_name_th", "last_name_th", "phone_number", "idcard", "email")


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate", "position", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("candidate__first_name_th", "candidate__last_name_th")
    raw_id_fields = ("candidate", "position")


@admin.register(EmployeeRecord)
class EmployeeRecordAdmin(admin.ModelAdmin):
    list_display = ("employee_code", "candidate", "start_date", "contract_type", "is_active")
    list_filter = ("is_active", "company", "contract_type")
    search_fields = ("employee_code", "candidate__first_name_th")


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "contract_type", "is_active", "uploaded_by", "updated_at")
    list_filter = ("contract_type", "is_active")
    search_fields = ("name",)


admin.site.register(Acquaintance)
admin.site.register(Guarantor)
admin.site.register(Study)
