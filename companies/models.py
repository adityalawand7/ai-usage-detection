from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255, blank=True)
    website = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Analysis Persistence Fields
    has_run_analysis = models.BooleanField(default=False)
    verdict = models.BooleanField(default=False)
    confidence = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=50, blank=True)
    maturity_score = models.IntegerField(default=0)
    summary = models.TextField(blank=True)
    
    capabilities = models.JSONField(default=list)
    evidence_summary = models.JSONField(default=dict)
    score_breakdown = models.JSONField(default=dict)
    raw_evidence = models.JSONField(default=list)
    
    last_analyzed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.website