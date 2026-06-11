from celery import shared_task

from analyzer.engine import analyze_company


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

    return result