import io
import os
import re
import cv2
import fitz
import docx
import openai
import base64
import easyocr
import numpy as np
from datetime import datetime
from .models import ChatEntry
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.files.storage import default_storage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import urllib.request

client = openai.OpenAI(api_key="API KEY HERE")
reader = easyocr.Reader(['en', 'hi'])

def extract_text_openai_from_base64_file_data(base64_full):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all visible text from this image."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_full,
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

def extract_text_easyocr_from_base64_data(base64_str):
    img_data = base64.b64decode(base64_str)
    img_array = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    results = reader.readtext(img, detail=0)
    return "\n".join(results)

def extract_patient_name(response_text):
    match = re.search(r'Patient Name:\s*(.+)', response_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Unknown"

def extract_text_from_file(uploaded_file):
    file_ext = os.path.splitext(uploaded_file.name)[-1].lower()
    if file_ext == '.txt':
        return uploaded_file.read().decode('utf-8')
    elif file_ext == '.docx':
        doc = docx.Document(uploaded_file)
        return '\n'.join([para.text for para in doc.paragraphs])
    elif file_ext == '.pdf':
        text = ""
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as pdf_file:
            for page in pdf_file:
                text += page.get_text()
        return text
    else:
        return None

def highlight_serious_words(text):
    serious_words = ['cancer', 'corona', 'covid', 'stroke', 'heart attack', 'tumor', 'malignant', 'severe', 'critical', 'emergency', 'fatal']
    highlighted_text = text
    for word in serious_words:
        highlighted_text = re.sub(r'\b' + re.escape(word) + r'\b', f'<font color="red"><b>{word}</b></font>', highlighted_text, flags=re.IGNORECASE)
    return highlighted_text

def count_nil_fields(response_text):
    nil_count = 0
    fields = [
        'Patient Name:', 'Age:', 'Gender:', 'Date of Admission:', 'Date of Discharge:',
        'Presenting Complaint:', 'Current Symptoms and Observations:', 'Previous Symptoms:',
        'Previous Medical History:', 'Social History:', 'Diagnosis:', 'Vitals:',
        'Medications:', 'Procedures/Interventions:', 'Lab Results:', 'Follow-up Instructions:'
    ]
    for field in fields:
        if re.search(fr'{field}\s*(Nil|nil|NIL|Unknown|unknown|UNKNOWN)', response_text):
            nil_count += 1
    return nil_count

@login_required
def index(request):
    response = None
    user_input = ''
    name_missing = False
    extracted_name = ''
    extracted_text_preview = ''
    chat_history = ChatEntry.objects.filter(user=request.user).order_by('-timestamp')[:10]

    for chat in chat_history:
        chat.patient_name = extract_patient_name(chat.response or "")
        chat.formatted_date = chat.timestamp.strftime('%d/%m/%y')

    if request.method == 'POST':
        user_input = request.POST.get('user_input', '')
        uploaded_file = request.FILES.get('uploaded_file')

        if uploaded_file:
            ext = os.path.splitext(uploaded_file.name)[-1].lower()

            if ext in ['.jpg', '.jpeg', '.png']:
                image_data = uploaded_file.read()
                base64_str = base64.b64encode(image_data).decode('utf-8')
                base64_full = f"data:image/jpeg;base64,{base64_str}"
                try:
                    gpt_ocr_text = extract_text_openai_from_base64_file_data(base64_full)
                except Exception as e:
                    gpt_ocr_text = f"⚠️ AI OCR failed: {e}"
                try:
                    easyocr_text = extract_text_easyocr_from_base64_data(base64_str)
                except Exception as e:
                    easyocr_text = f"⚠️ EasyOCR failed: {e}"

                extracted_text_preview = f"[OCR - AI]\n{gpt_ocr_text}\n\n[OCR - EasyOCR]\n{easyocr_text}"
                user_input += f"\n\n{extracted_text_preview}"

            elif ext in ['.pdf', '.txt', '.docx']:
                extracted_text = extract_text_from_file(uploaded_file)
                if extracted_text:
                    extracted_text_preview = extracted_text
                    user_input += "\n\n" + extracted_text
                else:
                    response = "⚠️ Unsupported file type. Please upload .pdf, .txt, or .docx"
                    return render(request, 'textprocessor/index.html', {
                        'user_input': user_input,
                        'response': response,
                        'chat_history': chat_history,
                        'username_cap': request.user.username.capitalize(),
                        'extracted_text_preview': extracted_text_preview,
                    })
            else:
                response = "⚠️ Unsupported file format."

        prompt = f"""You are an expert clinical assistant. From the following doctor-patient conversation or extracted note:
\n\"\"\"{user_input}\"\"\"
Extract and return a structured clinical note with these fields:

- Patient Name:
- Age:
- Gender:
- Date of Admission:
- Date of Discharge:
- Presenting Complaint:
- Current Symptoms and Observations:
- Previous Symptoms:
- Previous Medical History:
- Social History:
- Diagnosis:
- Vitals:
- Medications (with dosage, frequency):
- Procedures/Interventions:
- Lab Results:
- Follow-up Instructions:

Mention 'Nil' if any field is unavailable. Keep it clean and organized. Do not make up or presume any data."""

        try:
            chat_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful medical assistant. Be precise and only include information that is explicitly mentioned. Do not presume or invent any data."},
                    {"role": "user", "content": prompt}
                ]
            )
            response = chat_response.choices[0].message.content.strip()
        except Exception as e:
            response = f"⚠️ Error: {str(e)}"

        nil_count = count_nil_fields(response)
        if nil_count > 13:
            response = "⚠️ Insufficient data. Too many fields are Nil. Please provide more detailed information."
            return render(request, 'textprocessor/index.html', {
                'user_input': user_input,
                'response': response,
                'chat_history': chat_history,
                'username_cap': request.user.username.capitalize(),
                'extracted_text_preview': extracted_text_preview,
            })

        extracted_name = extract_patient_name(response)
        manual_name = request.POST.get('manual_name')
        if manual_name:
            response_lines = response.splitlines()
            for i, line in enumerate(response_lines):
                if line.lower().startswith("patient name:"):
                    response_lines[i] = f"Patient Name: {manual_name}"
                    break
            else:
                response_lines.insert(0, f"Patient Name: {manual_name}")
            response = "\n".join(response_lines)
            extracted_name = manual_name
        
        # Save chat only if a proper patient name is extracted
        extracted_name = extract_patient_name(response or "")
        name_missing = False

        if extracted_name.lower() not in ["nil", "unknown", ""]:
            ChatEntry.objects.create(user_input=user_input, response=response, user=request.user)
        else:
            name_missing = True

        chat_history = ChatEntry.objects.filter(user=request.user).order_by('-timestamp')[:10]
        for chat in chat_history:
            chat.patient_name = extract_patient_name(chat.response or "") or "Unknown"
            chat.formatted_date = chat.timestamp.strftime('%d/%m/%y')
            chat.case_filing_date = chat.timestamp


    return render(request, 'textprocessor/index.html', {
        'user_input': user_input,
        'response': response,
        'chat_history': chat_history,
        'name_missing': name_missing,
        'username_cap': request.user.username.capitalize(),
        'extracted_text_preview': extracted_text_preview,
    })

@login_required
def view_chat(request, chat_id):
    chat = get_object_or_404(ChatEntry, id=chat_id, user=request.user)
    chat.patient_name = extract_patient_name(chat.response or "")
    chat.formatted_date = chat.timestamp.strftime('%d/%m/%y')
    return render(request, 'textprocessor/view_chat.html', {'chat': chat})

@login_required
def edit_chat(request, chat_id):
    chat = get_object_or_404(ChatEntry, id=chat_id, user=request.user)
    if request.method == 'POST':
        chat.user_input = request.POST.get('user_input', chat.user_input)
        chat.response = request.POST.get('response', chat.response)
        chat.save()
        return redirect('view_chat', chat_id=chat.id)
    chat.patient_name = extract_patient_name(chat.response or "")
    chat.formatted_date = chat.timestamp.strftime('%d/%m/%y')
    return render(request, 'textprocessor/edit_chat.html', {'chat': chat})

@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(ChatEntry, id=chat_id, user=request.user)
    chat.delete()
    return redirect('index')

@login_required
def download_pdf(request):
    if request.method == 'POST':
        content = request.POST.get('pdf_content', 'No content provided')
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=72, bottomMargin=72)

        styles = getSampleStyleSheet()
        elements = []

        header_style = ParagraphStyle(
            name='Header',
            fontSize=20,
            textColor=colors.HexColor('#009688'),
            alignment=1,
            spaceAfter=12,
        )
        label_style = ParagraphStyle(
            name='Label',
            fontSize=12,
            leading=16,
            spaceAfter=6,
        )
        disclaimer_style = ParagraphStyle(
            name='Disclaimer',
            fontSize=9,
            textColor=colors.grey,
            alignment=1,
            spaceBefore=20,
        )

        try:
            logo_url = "https://iili.io/FRzYAdP.png"
            logo_temp = io.BytesIO(urllib.request.urlopen(logo_url).read())
            logo = Image(logo_temp, width=1*inch, height=1*inch)
            logo.hAlign = 'CENTER'
            elements.append(logo)
        except Exception as e:
            print(f"Logo load failed: {e}")

        elements.append(Paragraph("MediBrief", header_style))
        elements.append(Spacer(1, 12))

        highlighted_content = highlight_serious_words(content)
        for line in highlighted_content.splitlines():
            if line.strip():
                elements.append(Paragraph(line.strip(), label_style))

        elements.append(Spacer(1, 24))
        elements.append(Paragraph("This document is confidential and intended for medical purposes only.", disclaimer_style))

        doc.build(elements)
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf', headers={
            'Content-Disposition': 'attachment; filename="medical_summary.pdf"'
        })

@login_required
def download_chat_pdf(request, chat_id):
    chat = get_object_or_404(ChatEntry, id=chat_id, user=request.user)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    elements = []

    header_style = ParagraphStyle(
        name='Header',
        fontSize=20,
        textColor=colors.HexColor('#009688'),
        alignment=1,
        spaceAfter=12,
    )
    label_style = ParagraphStyle(
        name='Label',
        fontSize=12,
        leading=16,
        spaceAfter=6,
    )
    disclaimer_style = ParagraphStyle(
        name='Disclaimer',
        fontSize=9,
        textColor=colors.grey,
        alignment=1,
        spaceBefore=20,
    )

    try:
        logo_url = "https://iili.io/FRzYAdP.png"
        logo_temp = io.BytesIO(urllib.request.urlopen(logo_url).read())
        logo = Image(logo_temp, width=1*inch, height=1*inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)
    except Exception as e:
        print(f"Logo load failed: {e}")

    elements.append(Paragraph("MediBrief", header_style))
    elements.append(Spacer(1, 12))

    highlighted_content = highlight_serious_words(chat.response or "")
    for line in highlighted_content.splitlines():
        if line.strip():
            elements.append(Paragraph(line.strip(), label_style))

    elements.append(Spacer(1, 24))
    elements.append(Paragraph("This document is confidential and intended for medical purposes only.", disclaimer_style))

    doc.build(elements)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="summary_{chat_id}.pdf"'
    })

def login_view(request):
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            error_message = 'Invalid username or password.'
    return render(request, 'textprocessor/login.html', {'error_message': error_message})

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            error_message = 'Username already exists.'
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('index')
    return render(request, 'textprocessor/register.html', {'error_message': error_message})
