# Resume Skill Extractor

A web-based tool to extract structured data from PDF resumes, built with Python and Streamlit.

## Features
- **Upload PDF resumes** through a simple web GUI
- **Extracts**: Name, Email, Phone, Skills, and Work Experience
- **Tag resumes** with custom keywords
- **Browse, search, and filter** uploaded resumes by tags or keywords
- **Persistent storage**: Each resume is saved as a JSON file for later access

## Demo
Deploy this app instantly on [Streamlit Community Cloud](https://streamlit.io/cloud) or run locally.

---

## Getting Started

### 1. Clone the Repository
```sh
git clone https://github.com/palthepusaisahith/ResumeSkill-Extractor.git
cd ResumeSkill-Extractor
```

### 2. Install Requirements
```sh
pip install -r requirements.txt
```

### 3. Run the App
```sh
streamlit run app.py
```
By default, the app runs at [http://localhost:8501](http://localhost:8501)

---

## Deploy on Streamlit Community Cloud
1. Push this repo to your GitHub account.
2. Go to [https://streamlit.io/cloud](https://streamlit.io/cloud) and connect your repo.
3. Set the main file as `app.py` and deploy.

---

## Project Structure
```
ResumeSkill-Extractor/
├── app.py
├── requirements.txt
├── README.md
└── resumes/           # Created automatically for extracted data
```

---

## Example Usage
1. Go to the **Upload Resume** tab and upload a PDF.
2. Add tags (comma-separated) before saving.
3. Switch to **Browse & Search Resumes** to filter/search all uploaded resumes.

---

## License
This project is for educational and demonstration purposes.
