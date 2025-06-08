from django.db import models

class PDFDocument(models.Model):
    disease_name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='pdfs/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.disease_name} - {self.file_name}"
