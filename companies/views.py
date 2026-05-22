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

    if task.ready():

        return JsonResponse({
            "status": "completed",
            "result": task.result
        })

    return JsonResponse({
        "status": "running"
    })