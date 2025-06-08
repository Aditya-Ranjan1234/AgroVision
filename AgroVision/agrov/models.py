from django.db import models
from django.utils import timezone

# Create your models here.

class PredictionHistory(models.Model):
    PREDICTION_TYPES = [
        ('disease', 'Disease'),
        ('pest', 'Pest'),
    ]

    prediction_type = models.CharField(max_length=10, choices=PREDICTION_TYPES)
    image_url = models.URLField()
    label = models.CharField(max_length=100)
    confidence = models.FloatField()
    date_created = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=100, default='Chittoor')
    
    # Weather conditions at the time of prediction
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    soil_moisture = models.FloatField(null=True, blank=True)
    soil_ph = models.FloatField(null=True, blank=True)
    
    # Treatment recommendations
    treatment_plan = models.JSONField()

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.prediction_type} - {self.label} ({self.date_created.strftime('%Y-%m-%d %H:%M')})"
