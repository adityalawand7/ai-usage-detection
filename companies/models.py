from django.db import models

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=255, blank=True)
    website = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.website