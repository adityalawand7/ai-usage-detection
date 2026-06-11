from django.shortcuts import render
from django.http import JsonResponse

from celery.result import AsyncResult

from .tasks import run_analysis


def submit_company(request):

    context = {}

    if request.method == "POST":

        url = request.POST.get("url")

        if url:

            if not url.startswith("http"):
                url = "https://" + url

            task = run_analysis.delay(url)

            context["task_id"] = task.id

    return render(
        request,
        "companies/submit.html",
        context
    )


def task_status(request, task_id):

    task = AsyncResult(task_id)

    # --------------------------------
    # TASK COMPLETED
    # --------------------------------

    if task.ready():

        return JsonResponse({
            "status": "completed",
            "result": task.result
        })

    # --------------------------------
    # TASK IN PROGRESS
    # --------------------------------

    if task.state == "PROGRESS":

        return JsonResponse({
            "status": "running",
            "step": task.info.get("step"),
            "progress": task.info.get("progress")
        })

    # --------------------------------
    # TASK PENDING
    # --------------------------------

    return JsonResponse({
        "status": "pending"
    })