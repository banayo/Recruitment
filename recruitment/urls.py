from django.urls import path

from . import views

app_name = "recruitment"

urlpatterns = [
    path("", views.home, name="home"),
    path("requisitions/", views.requisition_list, name="requisition_list"),
    path("requisitions/new/", views.requisition_create, name="requisition_create"),
    path("requisitions/<int:pk>/", views.requisition_detail, name="requisition_detail"),
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
]
