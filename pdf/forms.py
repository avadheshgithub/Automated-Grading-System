from django import forms
from .models import PDFFile, GradingCriteria

class PDFFileForm(forms.ModelForm):
    class Meta:
        model = PDFFile
        fields = ('file',)

class GradingCriteriaForm(forms.ModelForm):
    class Meta:
        model = GradingCriteria
        fields = ['keywords', 'grading_type']

class KeywordForm(forms.ModelForm):
    class Meta:
        model = GradingCriteria
        fields = ('keywords', 'grading_type', 'min_words', 'max_words', 'manual_criteria')

        
# class GradingCriteriaForm(forms.ModelForm):
#     class Meta:
#         model = GradingCriteria
#         exclude = ['pdf']