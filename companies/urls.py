from django.urls import path

from .views import (
    submit_company,
    task_status
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
]