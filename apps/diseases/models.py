from django.db import models

class Disease(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    recommendation = models.TextField(blank=True, null=True)
    treatment_solutions = models.TextField(blank=True, null=True)
    recovery_steps = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.code} - {self.name}"
