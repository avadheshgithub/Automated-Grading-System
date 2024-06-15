from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_pdf, name='upload_pdf'),
    path('keyword_form/<int:pdf_id>/', views.keyword_form, name='keyword_form'),
    path('grade_pdf/<int:pdf_id>/', views.grade_pdf, name='grade_pdf'),
    path('show_extracted_text/<int:pdf_id>/', views.show_extracted_text, name='show_extracted_text'),
]
