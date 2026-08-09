from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Department, Division, JobPosition, Requisition, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "person_unid",
        "nickname",
        "company_code",
        "division",
        "department",
        "is_staff",
    )
    search_fields = ("username", "person_unid", "nickname", "authentik_sub", "email")
    ordering = ("person_unid",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "SSO / Profile",
            {
                "fields": (
                    "authentik_sub",
                    "person_unid",
                    "approve_code",
                    "gender",
                    "division",
                    "department",
                    "location",
                    "nickname",
                    "company_code",
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
                    "nickname",
                    "company_code",
                )
            },
        ),
    )


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ("division_code", "name")
    search_fields = ("division_code", "name")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("department_code", "name", "division")
    list_filter = ("division",)
    search_fields = ("department_code", "name")


@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = (
        "job_code",
        "title",
        "department",
        "current_headcount",
        "target_headcount",
    )
    list_filter = ("department",)
    search_fields = ("job_code", "title")


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
