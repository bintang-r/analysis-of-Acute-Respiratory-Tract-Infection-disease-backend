# pyrefly: ignore [missing-import]
from django.db import models

class HealthExpert(models.Model):
    name = models.CharField(max_length=255)
    profession = models.CharField(max_length=255)
    workplace = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
