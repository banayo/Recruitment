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
]
