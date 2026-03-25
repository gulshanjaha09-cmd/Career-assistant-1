
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pdfplumber
import re

app = FastAPI()

# Connect static folder (CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Connect templates folder (HTML)
templates = Jinja2Templates(directory="templates")

# ---------- SHOW HTML PAGE ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/resume", response_class=HTMLResponse)
def resume(request: Request):
    return templates.TemplateResponse("resume.html", {"request": request})

@app.get("/internships", response_class=HTMLResponse)
def internships(request: Request):
    return templates.TemplateResponse("internships.html", {"request": request})

@app.get("/apply", response_class=HTMLResponse)
def apply_page(request: Request):
    return templates.TemplateResponse("apply.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

# ---------- Extract text ----------
def extract_pdf_text(file):
    text = ""
    try:
        file.seek(0)   # 🔥 VERY IMPORTANT
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except Exception as e:
        print("PDF ERROR:", e)
        return ""
    return text.lower()


# ---------- Extract details ----------
def extract_details(text):
    lines = text.split("\n")
    name = "Not Found"

    for line in lines[:5]:   # check first 5 lines
      if len(line.split()) >= 2:  
          name = line
          break

    dob_match = re.search(r"\d{2}/\d{2}/\d{4}", text)
    dob = dob_match.group() if dob_match else "Not Found"

    return {"name": name.strip(), "dob": dob}


# ---------- Compare ----------
def compare_details(resume, cert):
    issues = []

    r_name = resume["name"].lower().strip()
    c_name = cert["name"].lower().strip()

    # Partial match allowed
    if r_name not in c_name and c_name not in r_name:
        issues.append("❌ Name mismatch")

    if resume["dob"] != cert["dob"]:
        issues.append("❌ DOB mismatch")

    if not issues:
        return "✅ All details match"

    return " | ".join(issues)

def analyze_resume(text):
    suggestions = []

    if "python" not in text:
        suggestions.append("⚠️ Add Python skill")

    if "project" not in text:
        suggestions.append("⚠️ Add projects")

    if len(text) < 300:
        suggestions.append("⚠️ Resume too short")

    if not suggestions:
        return "✅ Resume looks good"

    return " | ".join(suggestions)

# ---------- VERIFY API ----------
@app.post("/verify")
async def verify(resume: UploadFile = File(...), cert: UploadFile = File(...)):

    print("API CALLED")
   
    resume_text = extract_pdf_text(resume.file)
    cert_text = extract_pdf_text(cert.file)

    resume_data = extract_details(resume_text)
    cert_data = extract_details(cert_text)

    result = compare_details(resume_data, cert_data)
    analysis = analyze_resume(resume_text)

    return {
        "result": result,
        "analysis": analysis,
        "resume_data": resume_data,
        "certificate_data": cert_data
    }
