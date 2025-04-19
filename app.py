import streamlit as st
import fitz  # PyMuPDF
import re
import json
import tempfile
import os
import uuid
from datetime import datetime
from typing import List, Dict

# Function to extract text from PDF using PyMuPDF
def extract_pdf_text(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

# Function to parse resume text using regex
def parse_resume(text):
    # Extract full name (first non-empty line)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    full_name = lines[0] if lines else ""

    # Email regex
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else ""

    # Phone regex (US/international, simple version)
    phone_pattern = r'(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}'
    phone_match = re.search(phone_pattern, text)
    phone = phone_match.group(0) if phone_match else ""

    # --- Enhanced Skills Extraction ---
    skills_keywords = [
        "Python", "Java", "SQL", "Machine Learning", "Flask", "React", "NLP", "Deep Learning", "C++", "C#", "R", "Go", "Ruby", "PHP",
        "HTML", "CSS", "JavaScript", "Pandas", "NumPy", "TensorFlow", "Keras", "PyTorch", "Django", "FastAPI", "Tableau", "Excel",
        "Power BI", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux", "Shell", "Bash", "Spark", "Hadoop", "Scala",
        "Matplotlib", "Seaborn", "OpenCV", "Scikit-learn", "XGBoost", "LightGBM", "SQLAlchemy", "PostgreSQL", "MySQL", "MongoDB",
        "Firebase", "TypeScript", "Next.js", "Vue.js", "Angular", "Bootstrap", "SASS", "Redux", "REST API", "GraphQL"
    ]

    # 1. Try to extract from a "Skills" section
    skills_section = re.search(r"(?i)Skills\s*[:\-]?\s*(.+?)(?:\n[A-Z][^\n]*:|\n[A-Z][^\n]*\n|\Z)", text, re.DOTALL)
    skills_found = []
    if skills_section:
        # Get section text and split by comma or newline
        section_text = skills_section.group(1)
        # Split by comma or newline, strip whitespace
        skills_raw = re.split(r"[\n,•]", section_text)
        for skill in skills_raw:
            cleaned = skill.strip()
            # Only add if it's a known skill or looks like a skill (letters, 2+ chars)
            if cleaned and (cleaned in skills_keywords or re.match(r"^[A-Za-z0-9#\+\.\- ]{2,}$", cleaned)):
                skills_found.append(cleaned)
        # Deduplicate and keep order
        skills_found = list(dict.fromkeys(skills_found))

    # 2. Fallback: keyword search in whole text
    if not skills_found:
        for skill in skills_keywords:
            if re.search(r'\\b' + re.escape(skill) + r'\\b', text, re.IGNORECASE):
                skills_found.append(skill)

    # Work experience extraction
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


# Directory to store resumes
RESUME_DIR = "resumes"
os.makedirs(RESUME_DIR, exist_ok=True)

# Helper to load all resumes
def load_all_resumes() -> List[Dict]:
    resumes = []
    for fname in os.listdir(RESUME_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(RESUME_DIR, fname), encoding="utf-8") as f:
                data = json.load(f)
                data["_filename"] = fname
                resumes.append(data)
    return resumes

# Helper to save a resume
def save_resume(data: dict, tags: List[str]):
    data["tags"] = tags
    data["uploaded_at"] = datetime.now().isoformat()
    resume_id = str(uuid.uuid4())
    fname = f"resume_{resume_id}.json"
    with open(os.path.join(RESUME_DIR, fname), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return fname

# Streamlit app with sidebar for search/filter

def main():
    st.set_page_config(page_title="Resume Extractor App", layout="wide")
    st.title("Resume Extractor App")
    st.write("Upload a PDF resume to extract key information. Tag and search through all uploads.")

    # Tabs: Upload / Browse
    tab1, tab2 = st.tabs(["Upload Resume", "Browse & Search Resumes"])

    with tab1:
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
        tags = st.text_input("Add tags (comma-separated)", "")
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]

        if uploaded_file is not None:
            # Save uploaded file to a temp location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

            # Extract text
            with st.spinner('Extracting text from PDF...'):
                text = extract_pdf_text(tmp_path)

            # Parse resume
            with st.spinner('Parsing resume information...'):
                result = parse_resume(text)

            st.subheader("Extracted Resume Data:")
            st.json(result)

            st.subheader("Extracted Raw Text (Debug)")
            st.text_area("Raw Resume Text", text, height=300)

            if st.button("Save Resume Data"):
                fname = save_resume(result, tags_list)
                st.success(f"Resume data saved as {fname}")

    with tab2:
        st.header("All Uploaded Resumes")
        resumes = load_all_resumes()
        if not resumes:
            st.info("No resumes uploaded yet.")
            return

        # Collect all tags
        all_tags = set()
        for r in resumes:
            all_tags.update(r.get("tags", []))
        all_tags = sorted(list(all_tags))

        # Sidebar filters
        search_term = st.text_input("Search (name, skill, etc.)", "")
        selected_tags = st.multiselect("Filter by tags", all_tags)

        # Filtering logic
        def resume_matches(resume):
            # Search term in name, email, skills, experience
            if search_term:
                term = search_term.lower()
                searchable = " ".join([
                    str(resume.get("full_name", "")),
                    str(resume.get("email", "")),
                    str(resume.get("skills", [])),
                    str(resume.get("work_experience", ""))
                ]).lower()
                if term not in searchable:
                    return False
            # Tags
            if selected_tags:
                resume_tags = set(resume.get("tags", []))
                if not set(selected_tags).issubset(resume_tags):
                    return False
            return True

        filtered_resumes = [r for r in resumes if resume_matches(r)]

        st.write(f"Found {len(filtered_resumes)} resumes.")

        for r in filtered_resumes:
            with st.expander(f"{r.get('full_name', 'Unknown Name')} | {r.get('email', '')} | Tags: {', '.join(r.get('tags', []))}"):
                st.json({
                    'Full Name': r.get('full_name', ''),
                    'Email': r.get('email', ''),
                    'Phone': r.get('phone', ''),
                    'Skills': r.get('skills', []),
                    'Work Experience': r.get('work_experience', ''),
                    'Tags': r.get('tags', []),
                    'Uploaded At': r.get('uploaded_at', '')
                })

if __name__ == "__main__":
    main()
