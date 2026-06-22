from django.shortcuts import render
from django.http import JsonResponse

from celery.result import AsyncResult

from .tasks import run_analysis
from .models import Company


def submit_company(request):

    context = {}

    # Fetch successful historical scans for the dashboard
    history = Company.objects.filter(
        has_run_analysis=True
    ).order_by("-last_analyzed")[:15]
    
    context["history"] = history

    if request.method == "POST":

        raw_url = request.POST.get("url", "").strip().lower()
        recheck = request.POST.get("recheck") == "true"

        if raw_url:
            
            # Standardize scheme
            if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
                url_with_scheme = "https://" + raw_url
            else:
                url_with_scheme = raw_url

            # Extract host and strip 'www.'
            from urllib.parse import urlparse
            try:
                parsed = urlparse(url_with_scheme)
                host = parsed.netloc
                if host.startswith("www."):
                    host = host[4:]
                
                # Canonical url format: https://domain
                url = f"https://{host}"
            except Exception:
                url = url_with_scheme.rstrip("/")

            # Check if domain is a UGC or job board platform
            UGC_DOMAINS = [
                "linkedin.com", "reddit.com", "medium.com", "facebook.com", 
                "twitter.com", "x.com", "instagram.com", "youtube.com", 
                "vimeo.com", "quora.com", "pinterest.com", "tumblr.com", 
                "github.com", "stackoverflow.com", "dev.to", "wikipedia.org",
                "indeed.com", "glassdoor.com", "ziprecruiter.com", "monster.com",
                "simplyhired.com", "careerbuilder.com", "dice.com", "wellfound.com"
            ]
            
            is_ugc = any(ugc in host for ugc in UGC_DOMAINS)

            if is_ugc:
                context["error"] = "Scanning platforms with high user-generated content (UGC) or job boards is disabled to prevent misleading AI usage detection."
            else:
                # Caching check
                existing = Company.objects.filter(
                    website=url,
                    has_run_analysis=True
                ).first()

                if existing and not recheck:
                    # Direct immediate rendering using DB cache
                    context["cached_company_id"] = existing.id
                else:
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

        if task.status == "FAILURE":
            return JsonResponse({
                "status": "failed",
                "message": str(task.result)
            })

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


def get_company_report(request, company_id):

    try:
        company = Company.objects.get(pk=company_id)
        
        return JsonResponse({
            "status": "completed",
            "result": {
                "url": company.website,
                "verdict": company.verdict,
                "confidence": company.confidence,
                "role": company.role,
                "maturity_score": company.maturity_score,
                "total_score": company.maturity_score,
                "summary": company.summary,
                "capabilities": company.capabilities,
                "evidence_summary": company.evidence_summary,
                "score_breakdown": company.score_breakdown,
                "evidence": company.raw_evidence,
            }
        })

    except Company.DoesNotExist:
        
        return JsonResponse(
            {"status": "error", "message": "Company not found"},
            status=404
        )