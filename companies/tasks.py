from celery import shared_task

from analyzer.engine import analyze_company
from companies.models import Company


@shared_task(bind=True)
def run_analysis(self, url):

    # --------------------------------
    # INITIAL TASK STATE
    # --------------------------------

    self.update_state(
        state="PROGRESS",
        meta={
            "step": "Initializing analysis",
            "progress": 5
        }
    )

    result = analyze_company(
        url,
        task=self
    )

    # --------------------------------
    # SERIALIZE EVIDENCE
    # --------------------------------

    serialized = []

    for e in result["evidence"]:

        serialized.append({
            "url": e.url,
            "page_type": e.page_type,
            "text": e.text,
            "similarity": e.similarity,
            "strength": e.strength,
            "category": e.category,
        })

    result["evidence"] = serialized

    # --------------------------------
    # PERSIST TO DATABASE
    # --------------------------------
    try:
        company, created = Company.objects.get_or_create(website=url)
        company.has_run_analysis = True
        company.verdict = result["verdict"]
        company.confidence = result["confidence"]
        company.role = result["role"]
        company.maturity_score = result["maturity_score"]
        company.summary = result["summary"]
        company.capabilities = result.get("capabilities", [])
        company.evidence_summary = result["evidence_summary"]
        company.score_breakdown = result["score_breakdown"]
        company.raw_evidence = serialized
        company.save()
    except Exception as e:
        print(f"[Celery Task] Error saving company report to DB: {e}")

    return result