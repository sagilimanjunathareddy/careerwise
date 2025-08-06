import fitz  # PyMuPDF
import re
import spacy

nlp = spacy.load("en_core_web_sm")

SKILL_KEYWORDS = [
    "Python", "Java", "C++", "Machine Learning", "Deep Learning", "Data Science",
    "Django", "Flask", "React", "SQL", "MongoDB", "Git", "HTML", "CSS", "JavaScript"
]

def extract_text_from_pdf(filepath):
    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_email(text):
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None

def extract_phone(text):
    match = re.search(r"(\+91[\-\s]?)?[789]\d{9}", text)
    return match.group(0) if match else None

def extract_linkedin(text):
    match = re.search(r"https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?", text)
    return match.group(0) if match else None

def extract_skills(text):
    doc = nlp(text)
    return list(set([token.text for token in doc if token.text in SKILL_KEYWORDS]))

def extract_education(text):
    pattern = r"(B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc|Bachelor|Master|Ph\.?D).*?(?=\n|,|\.)"
    return list(set(re.findall(pattern, text, flags=re.IGNORECASE)))

def extract_experience(text):
    pattern = r"(\d+)\+?\s*(years|yrs|year)\s*(of)?\s*(experience)?"
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    return [f"{m[0]} years" for m in matches]

def calculate_resume_score(skills, education, experience, email, phone, linkedin):
    score = 0
    if skills: score += min(len(skills), 10) * 2  # Max 20
    if education: score += 20
    if experience: score += 20
    if email: score += 10
    if phone: score += 10
    if linkedin: score += 20
    return min(score, 100)

def parse_resume(filepath):
    text = extract_text_from_pdf(filepath)

    email = extract_email(text)
    phone = extract_phone(text)
    linkedin = extract_linkedin(text)
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)
    score = calculate_resume_score(skills, education, experience, email, phone, linkedin)

    return {
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "skills": skills,
        "education": education,
        "experience": experience,
        "score": score
    }
