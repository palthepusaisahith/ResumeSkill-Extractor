from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import fitz  # PyMuPDF
import re
import json
import os
import uuid
from datetime import datetime

app = FastAPI()

# Allow frontend to call backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESUME_DIR = "resumes"
os.makedirs(RESUME_DIR, exist_ok=True)

# --- Resume Parsing Logic (from your app.py) ---
def extract_pdf_text(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def parse_resume(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    full_name = lines[0] if lines else ""

    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else ""

    phone_pattern = r'(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}'
    phone_match = re.search(phone_pattern, text)
    phone = phone_match.group(0) if phone_match else ""

    skills_keywords = [
        "Python", "Java", "SQL", "Machine Learning", "Flask", "React", "NLP", "Deep Learning", "C++", "C#", "R", "Go", "Ruby", "PHP",
        "HTML", "CSS", "JavaScript", "Pandas", "NumPy", "TensorFlow", "Keras", "PyTorch", "Django", "FastAPI", "Tableau", "Excel",
        "Power BI", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux", "Shell", "Bash", "Spark", "Hadoop", "Scala",
        "Matplotlib", "Seaborn", "OpenCV", "Scikit-learn", "XGBoost", "LightGBM", "SQLAlchemy", "PostgreSQL", "MySQL", "MongoDB",
        "Firebase", "TypeScript", "Next.js", "Vue.js", "Angular", "Bootstrap", "SASS", "Redux", "REST API", "GraphQL"
    ]
    skills_section = re.search(r"(?i)Skills\s*[:\-]?\s*(.+?)(?:\n[A-Z][^\n]*:|\n[A-Z][^\n]*\n|\Z)", text, re.DOTALL)
    skills_found = []
    if skills_section:
        section_text = skills_section.group(1)
        skills_raw = re.split(r"[\n,•]", section_text)
        for skill in skills_raw:
            cleaned = skill.strip()
            if cleaned and (cleaned in skills_keywords or re.match(r"^[A-Za-z0-9#\+\.\- ]{2,}$", cleaned)):
                skills_found.append(cleaned)
        skills_found = list(dict.fromkeys(skills_found))
    if not skills_found:
        for skill in skills_keywords:
            if re.search(r'\\b' + re.escape(skill) + r'\\b', text, re.IGNORECASE):
                skills_found.append(skill)
    exp_headings = ['Experience', 'Work History', 'Professional Background']
    exp_pattern = r'(?i)(' + '|'.join(re.escape(h) for h in exp_headings) + r')\s*[\n\r]+(.*?)(?:\n[A-Z][^\n]+:|\Z)'
    exp_match = re.search(exp_pattern, text, re.DOTALL)
    work_experience = exp_match.group(2).strip() if exp_match else ""
    return {
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'skills': skills_found,
        'work_experience': work_experience
    }

# --- API Endpoints ---
@app.post("/api/upload_resume")
async def upload_resume(pdf: UploadFile = File(...), tags: str = Form("")):
    # Save uploaded PDF to temp file
    temp_path = f"/tmp/{uuid.uuid4()}.pdf"
    with open(temp_path, "wb") as f:
        f.write(await pdf.read())
    text = extract_pdf_text(temp_path)
    result = parse_resume(text)
    os.remove(temp_path)
    return {"result": result, "raw_text": text}

@app.post("/api/save_resume")
async def save_resume(data: dict):
    tags = data.get("tags", [])
    data["tags"] = tags
    data["uploaded_at"] = datetime.now().isoformat()
    resume_id = str(uuid.uuid4())
    fname = f"resume_{resume_id}.json"
    with open(os.path.join(RESUME_DIR, fname), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"filename": fname}

@app.get("/api/resumes")
def get_resumes(search: Optional[str] = None, tags: Optional[str] = None):
    resumes = []
    for fname in os.listdir(RESUME_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(RESUME_DIR, fname), encoding="utf-8") as f:
                data = json.load(f)
                data["_filename"] = fname
                resumes.append(data)
    # Filtering
    if search:
        term = search.lower()
        resumes = [r for r in resumes if term in (r.get("full_name", "") + " " + r.get("email", "") + " " + " ".join(r.get("skills", [])) + " " + r.get("work_experience", "")).lower()]
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        resumes = [r for r in resumes if set(tag_list).issubset(set(r.get("tags", [])))]
    return resumes
