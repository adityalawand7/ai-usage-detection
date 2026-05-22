from celery import shared_task

from analyzer.engine import analyze_company


@shared_task
def run_analysis(url):

    result = analyze_company(url)

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