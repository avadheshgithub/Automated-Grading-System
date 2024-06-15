# import os
# import pdfplumber
# import nltk
# from django.shortcuts import render, redirect, get_object_or_404
# from django.conf import settings
# from .forms import PDFFileForm, KeywordForm
# from .models import PDFFile, GradingCriteria
# from transformers import pipeline
# from django.http import HttpResponse

# # Ensure required NLTK data is downloaded
# nltk.download('stopwords')
# nltk.download('punkt')
# from nltk.corpus import stopwords
# from nltk.tokenize import word_tokenize
# import string

# def clean_text(text):
#     stop_words = set(stopwords.words('english'))
#     words = word_tokenize(text)
#     cleaned_words = [word for word in words if word.lower() not in stop_words and word not in string.punctuation]
#     return ' '.join(cleaned_words)

# def extract_text_from_pdf(pdf_path):
#     text = ""
#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages:
#             page_text = page.extract_text()
#             if page_text:
#                 text += page_text + "\n"
    
#     cleaned_text = clean_text(text)
#     return cleaned_text

# def upload_pdf(request):
#     if request.method == 'POST':
#         form = PDFFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             pdf_file = form.save()
#             return redirect('show_extracted_text', pdf_id=pdf_file.id)
#     else:
#         form = PDFFileForm()
#     return render(request, 'upload.html', {'form': form})

# def show_extracted_text(request, pdf_id):
#     pdf_file = get_object_or_404(PDFFile, id=pdf_id)
#     file_path = os.path.join(settings.MEDIA_ROOT, pdf_file.file.name)
#     extracted_text = extract_text_from_pdf(file_path)
#     num_words = len(extracted_text.split())  # Counting the number of words

#     # Create GradingCriteria if it doesn't exist
#     grading_criteria, created = GradingCriteria.objects.get_or_create(pdf=pdf_file)
    
#     return render(request, 'show_extracted_text.html', {'text': extracted_text, 'pdf_id': pdf_id, 'num_words': num_words})

# def keyword_form(request, pdf_id):
#     pdf_file = get_object_or_404(PDFFile, id=pdf_id)
#     grading_criteria, created = GradingCriteria.objects.get_or_create(pdf=pdf_file)
    
#     if request.method == 'POST':
#         form = KeywordForm(request.POST, instance=grading_criteria)
#         if form.is_valid():
#             form.save()
#             return redirect('grade_pdf', pdf_id=pdf_id)
#     else:
#         form = KeywordForm(instance=grading_criteria)
#     return render(request, 'keyword_form.html', {'form': form, 'pdf_id': pdf_id})

# def grade_pdf(request, pdf_id):
#     pdf_file = get_object_or_404(PDFFile, id=pdf_id)
#     grading_criteria = pdf_file.criteria
#     file_path = os.path.join(settings.MEDIA_ROOT, pdf_file.file.name)
#     extracted_text = extract_text_from_pdf(file_path)
    
#     # Calculate grade and score based on grading criteria
#     grade, score = calculate_grade_and_score(extracted_text, grading_criteria)
    
#     return render(request, 'result.html', {'text': extracted_text, 'grade': grade, 'score': score})

# def calculate_grade_and_score(text, grading_criteria):
#     # Load pre-trained BERT model for question answering
#     model = pipeline('question-answering', model="distilbert-base-uncased-distilled-squad")
    
#     keywords = grading_criteria.keywords.split(',')
#     min_words = grading_criteria.min_words
#     max_words = grading_criteria.max_words
    
#     # Count the occurrence of keywords in the text
#     keyword_count = sum(text.lower().count(keyword.lower()) for keyword in keywords)
    
#     # Calculate the length score based on the ratio of actual words to the specified word range
#     words = text.split()
#     total_words = len(words)
    
#     # Check if the total words are within the specified range
#     if total_words < min_words:
#         length_score = 0  # Penalty for too few words
#     elif total_words > max_words:
#         length_score = 50  # Adjust score for too many words
#     else:
#         length_score = (total_words / max_words) * 100
    
#     # Use the model to assess the quality of the answer
#     qa_input = {
#         'question': 'How relevant is this text to the given keywords?',
#         'context': text
#     }
#     model_output = model(qa_input)
#     relevance_score = model_output['score'] * 100
    
#     # Normalize scores and combine them
#     keyword_score = (keyword_count / len(keywords)) * 100 if keywords else 0
#     length_score = min(length_score, 100)
#     relevance_score = min(relevance_score, 100)
    
#     # Combine the scores based on your weighting criteria
#     score = (keyword_score + length_score + relevance_score) / 3
    
#     # Ensure score is within 0 to 100 range
#     score = min(max(score, 0), 100)
    
#     # Determine grade based on score
#     if score >= 90:
#         grade = 'S'
#     elif score >= 75:
#         grade = 'A'
#     elif score >= 60:
#         grade = 'B'
#     elif score >= 50:
#         grade = 'D'
#     elif score >= '35':
#         grade = 'F'
#     else:
#         grade = 'F'
    
#     if total_words == 0:
#         grade = 'N'  # Not attended
    
#     return grade, score


import os
import pdfplumber
import nltk
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from .forms import PDFFileForm, KeywordForm
from .models import PDFFile, GradingCriteria
from transformers import BertTokenizer, BertForQuestionAnswering
import torch

# Ensure required NLTK data is downloaded
nltk.download('stopwords')
nltk.download('punkt')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

def clean_text(text):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text)
    cleaned_words = [word for word in words if word.lower() not in stop_words and word not in string.punctuation]
    return ' '.join(cleaned_words)

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    cleaned_text = clean_text(text)
    return cleaned_text

def upload_pdf(request):
    if request.method == 'POST':
        form = PDFFileForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.save()
            return redirect('show_extracted_text', pdf_id=pdf_file.id)
    else:
        form = PDFFileForm()
    return render(request, 'upload.html', {'form': form})

def show_extracted_text(request, pdf_id):
    pdf_file = get_object_or_404(PDFFile, id=pdf_id)
    file_path = os.path.join(settings.MEDIA_ROOT, pdf_file.file.name)
    extracted_text = extract_text_from_pdf(file_path)
    num_words = len(extracted_text.split())  # Counting the number of words

    # Create GradingCriteria if it doesn't exist
    grading_criteria, created = GradingCriteria.objects.get_or_create(pdf=pdf_file)
    
    return render(request, 'show_extracted_text.html', {'text': extracted_text, 'pdf_id': pdf_id, 'num_words': num_words})

def keyword_form(request, pdf_id):
    pdf_file = get_object_or_404(PDFFile, id=pdf_id)
    grading_criteria, created = GradingCriteria.objects.get_or_create(pdf=pdf_file)
    
    if request.method == 'POST':
        form = KeywordForm(request.POST, instance=grading_criteria)
        if form.is_valid():
            form.save()
            return redirect('grade_pdf', pdf_id=pdf_id)
    else:
        form = KeywordForm(instance=grading_criteria)
    return render(request, 'keyword_form.html', {'form': form, 'pdf_id': pdf_id})

def grade_pdf(request, pdf_id):
    pdf_file = get_object_or_404(PDFFile, id=pdf_id)
    grading_criteria = pdf_file.criteria
    file_path = os.path.join(settings.MEDIA_ROOT, pdf_file.file.name)
    extracted_text = extract_text_from_pdf(file_path)
    
    # Calculate grade and score based on grading criteria
    grade, score = calculate_grade_and_score(extracted_text, grading_criteria)
    
    return render(request, 'result.html', {'text': extracted_text, 'grade': grade, 'score': score})

def calculate_grade_and_score(text, grading_criteria):
    # Load pre-trained BERT model and tokenizer for question answering
    model_name = "bert-base-uncased"
    model = BertForQuestionAnswering.from_pretrained(model_name)
    tokenizer = BertTokenizer.from_pretrained(model_name)

    # Define QA input and tokenize it
    question = "How relevant is this text to the given keywords?"
    inputs = tokenizer(question, text, return_tensors="pt", max_length=512, truncation=True)

    # Perform question answering
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Extract score from model outputs
    relevance_score = outputs["start_logits"].mean().item() * 100  # Adjust based on your specific use case
    
    # Calculate keyword count
    keywords = grading_criteria.keywords.split(',')
    keyword_count = sum(text.lower().count(keyword.lower()) for keyword in keywords)
    
    # Calculate length score based on word count
    words = text.split()
    total_words = len(words)
    min_words = grading_criteria.min_words
    max_words = grading_criteria.max_words
    if total_words < min_words:
        length_score = 0
    elif total_words > max_words:
        length_score = 50
    else:
        length_score = ((total_words - min_words) / (max_words - min_words)) * 50 + 50
    
    # Combine the scores based on your weighting criteria
    score = (relevance_score + keyword_count + length_score) / 3
    
    # Ensure score is within 0 to 100 range
    score = min(max(score, 0), 100)
    
    # Determine grade based on score
    if score >= 90:
        grade = 'A'
    elif score >= 75:
        grade = 'B'
    elif score >= 60:
        grade = 'C'
    elif score >= 50:
        grade = 'D'
    else:
        grade = 'F'
    
    if total_words == 0:
        grade = 'N'  # Not attended
    
    return grade, score
