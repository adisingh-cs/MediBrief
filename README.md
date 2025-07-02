# MediBrief - AI-Powered Clinical Note Generator  

![MediBrief Logo](https://iili.io/FRzYAdP.png)

**MediBrief** is a Django-based web application that helps healthcare professionals generate structured clinical notes from unstructured patient data — including text, images (JPEG/PNG), PDFs, and DOCX files.  
It leverages **OpenAI's GPT-4o/GPT-3.5-turbo** for advanced AI-powered note generation and **EasyOCR** for multilingual OCR (English/Hindi) support.

---

## ✨ Features

- **Text Extraction**
  - Supports JPEG/PNG images, PDFs, DOCX, and TXT files.
  - Uses GPT-4o for high-accuracy OCR and EasyOCR as fallback.
  
- **Structured Clinical Notes**
  - Automatically generates 16 standardized fields (e.g., Patient Name, Diagnosis, Medications).
  - Highlights critical terms (e.g., _cancer_, _stroke_) in red for urgency.
  
- **User Management**
  - Secure login and registration with Django's built-in authentication.
  
- **Note Management**
  - View, edit, delete, and export notes as professional PDFs.
  - Tracks note history with patient names and timestamps.

---

## 🛠️ Tech Stack

- **Backend:** Django (Python)  
- **AI & OCR:** OpenAI API (GPT-4o / GPT-3.5-turbo), EasyOCR, PyMuPDF  
- **Frontend:** HTML, CSS, Bootstrap  
- **Database:** SQLite (default)  
- **PDF Generation:** ReportLab  

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- OpenAI API Key → [Get one here](https://platform.openai.com/)

### Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/adisingh-cs/medibrief.git
   cd medibrief

2. **Set Up a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate   # For Linux/macOS
   venv\Scripts\activate      # For Windows

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt

4. **Configure OpenAI API Key**

   - Open views.py and set your API key:

   ```bash
   client = openai.OpenAI(api_key="your-api-key-here")

5. **Apply Migrations & Run the Server**

   ```bash
   python manage.py migrate
   python manage.py runserver

- Open your browser at: http://127.0.0.1:8000


## 📂 Project Structure

medibrief/
├── textprocessor/
│   ├── views.py           # Core logic (AI, OCR, PDF generation)
│   ├── models.py          # Database models
│   ├── templates/         # HTML templates
│   └── ...
├── manage.py              # Django CLI
└── requirements.txt       # Project dependencies


## 🤖 How It Works

- User uploads a file (image, PDF, DOCX) or inputs text.

- OCR and AI extract and structure the content into a clinical note.

- The user can edit, save, or export the note as a PDF.

- Notes are securely stored with history tracking for future access.

## 👥 MediBrief Contributors

This project was created during a hackathon to streamline clinical note generation using AI and OCR. Below are the individuals who contributed to the development of 


## 🚀 Project Lead

**Aditya Singh**  
- Role: Project Manager, Backend Developer (Django) 
- GitHub: [@adisingh-cs](https://github.com/adisingh-cs)

---

## 💡 Contributors

**[Dhruv Gupta]**  
- Role: Frontend Developer, UI/UX Designer  
- GitHub: [@Atheris29](https://github.com/Atheris29)

**[Anchal Maheshwari]**  
- Role: OCR Pipeline & PDF Handling
- GitHub: [@AnchalMaheshwari16](https://github.com/AnchalMaheshwari16)

**[Akanksha Gupta]**  
- Role: AI Integration,Easy OCR Integration, Documentation, Testing
- GitHub: [@Agupta163](https://github.com/Agupta163)

---

> 🙌 Huge thanks to everyone who contributed their time and skills to make MediBrief a success!

