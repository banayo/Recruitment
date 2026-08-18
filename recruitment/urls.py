from django.urls import path

from . import views

app_name = "recruitment"

urlpatterns = [
    path("", views.home, name="home"),
    path("requisitions/", views.requisition_list, name="requisition_list"),
    path("requisitions/new/", views.requisition_create, name="requisition_create"),
    path("requisitions/<int:pk>/", views.requisition_detail, name="requisition_detail"),
    path(
        "requisitions/<int:pk>/edit/",
        views.requisition_edit,
        name="requisition_edit",
    ),
    path(
        "requisitions/<int:pk>/approve/",
        views.requisition_approve,
        name="requisition_approve",
    ),
    path(
        "requisitions/<int:pk>/reject/",
        views.requisition_reject,
        name="requisition_reject",
    ),
    path(
        "requisitions/<int:pk>/hr-map/",
        views.requisition_hr_map,
        name="requisition_hr_map",
    ),
    path("approvals/", views.approval_inbox, name="approval_inbox"),
    path("my-positions/", views.my_positions, name="my_positions"),
    path("line/connect/", views.line_connect, name="line_connect"),
    path("line/callback/", views.line_callback, name="line_callback"),
    path("line/disconnect/", views.line_disconnect, name="line_disconnect"),
    # Master data
    path("divisions/", views.division_list, name="division_list"),
    path("divisions/new/", views.division_create, name="division_create"),
    path("divisions/<int:pk>/edit/", views.division_edit, name="division_edit"),
    path("departments/", views.department_list, name="department_list"),
    path("departments/new/", views.department_create, name="department_create"),
    path("departments/<int:pk>/edit/", views.department_edit, name="department_edit"),
    path("positions/", views.position_list, name="position_list"),
    path("positions/new/", views.position_create, name="position_create"),
    path("positions/<int:pk>/edit/", views.position_edit, name="position_edit"),
    path("companies/", views.company_list, name="company_list"),
    path("companies/new/", views.company_create, name="company_create"),
    path("companies/<int:pk>/edit/", views.company_edit, name="company_edit"),
    path("locations/", views.work_location_list, name="work_location_list"),
    path("locations/new/", views.work_location_create, name="work_location_create"),
    path(
        "locations/<int:pk>/edit/",
        views.work_location_edit,
        name="work_location_edit",
    ),
    path("levels/", views.employee_level_list, name="employee_level_list"),
    path("levels/new/", views.employee_level_create, name="employee_level_create"),
    path(
        "levels/<int:pk>/edit/",
        views.employee_level_edit,
        name="employee_level_edit",
    ),
    path("candidates/", views.list_candidate, name="list_candidate"),
    path(
        "candidates/address-lookup/",
        views.lookup_thai_address,
        name="lookup_thai_address",
    ),
    path("candidates/<int:pk>/edit/", views.candidate_edit, name="candidate_edit"),
    path("applications/", views.list_job_application, name="list_job_application"),
    path(
        "applications/<int:pk>/edit/",
        views.job_application_edit,
        name="job_application_edit",
    ),
    path(
        "applications/<int:pk>/",
        views.job_application_detail,
        name="job_application_detail",
    ),
    path(
        "applications/<int:application_id>/schedule/",
        views.schedule_interview,
        name="schedule_interview",
    ),
    path(
        "applications/<int:application_id>/start-work/",
        views.schedule_start_work,
        name="schedule_start_work",
    ),
    path("candidates/check/", views.check_candidate, name="check_candidate"),
    path(
        "candidates/new/",
        views.create_new_candidate,
        name="create_new_candidate",
    ),
    path(
        "candidate/<int:candidate_id>/apply/",
        views.create_application_for_existing,
        name="create_application_for_existing",
    ),
]
