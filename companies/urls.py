from django.urls import path

from .views import (
    submit_company,
    task_status,
    get_company_report
)

urlpatterns = [

    path(
        "",
        submit_company,
        name="submit_company"
    ),

    path(
        "task/<str:task_id>/",
        task_status,
        name="task_status"
    ),

    path(
        "company/<int:company_id>/",
        get_company_report,
        name="get_company_report"
    ),
]