from django.db import models
from django.utils import timezone
from django.db import migrations
from django import forms

class PDFFile(models.Model):
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

def set_default_uploaded_at(apps, schema_editor):
    PDFFile = apps.get_model('your_app_name', 'PDFFile')
    PDFFile.objects.update(uploaded_at=timezone.now())

class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0002_pdffile_uploaded_at_gradingcriteria'),
    ]

    operations = [
        migrations.RunPython(set_default_uploaded_at),
    ]


class GradingCriteria(models.Model):
    pdf = models.OneToOneField(PDFFile, on_delete=models.CASCADE, related_name='criteria')
    keywords = models.TextField()
    min_words = models.IntegerField(default=0)
    max_words = models.IntegerField(default=0)
    GRADING_TYPE_CHOICES = [
        ('relative', 'Relative'),
        ('absolute', 'Absolute'),
        ('manual', 'Manual')
    ]
    grading_type = models.CharField(max_length=10, choices=GRADING_TYPE_CHOICES, default='manual')
    manual_criteria = models.CharField(max_length=255, blank=True, null=True)

