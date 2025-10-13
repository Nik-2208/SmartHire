import os
import re
import io
import joblib
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from textblob import TextBlob
from difflib import SequenceMatcher

# ---------------- Setup ----------------
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

candidates = []
job_description_data = {}

# ---------------- Load Pretrained Model ----------------
MODEL_PATH = "resume_analyzer.pkl"
clf, le = joblib.load(MODEL_PATH)

# ---------------- Utilities ----------------
def clean_text(txt):
    if not isinstance(txt, str):
        return ""
    txt = txt.lower()
    txt = re.sub(r'\s+', ' ', txt)
    return txt.strip()

# ---------------- Resume Text Extraction ----------------
def extract_text_from_pdf(file_bytes):
    try:
        import fitz
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        return "".join([page.get_text() for page in pdf])
    except:
        return ""

def extract_text_from_docx(file_bytes):
    text = ""
    try:
        import tempfile
        from docx import Document
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            doc = Document(tmp.name)
            text = "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print("DOCX extraction error:", e)
    return text

def extract_text_from_txt(file_bytes):
    try:
        return file_bytes.decode('utf-8')
    except:
        return ""

def extract_text_from_image(file_bytes):
    try:
        from PIL import Image
        import easyocr
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        reader = easyocr.Reader(['en'], gpu=False)
        import numpy as np
        img_np = np.array(image)
        result = reader.readtext(img_np, detail=0)
        return " ".join(result)
    except:
        return ""

def grammar_check(text):
    blob = TextBlob(text)
    spelling_errors = sum(1 for word in blob.words if word.correct() != word)
    grammar_errors = 0
    return grammar_errors, spelling_errors

# ---------------- Resume Parsing ----------------
def extract_skills(text):
    skills_list = ["python","java","c++","sql","aws","docker","flask","django","react","javascript","html","css"]
    text = clean_text(text)
    return [s for s in skills_list if s in text]

def estimate_experience(text):
    exp_years = 0
    ranges = re.findall(r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)', text, re.IGNORECASE)
    for start, end in ranges:
        try:
            start = int(start)
            end = datetime.now().year if re.search("present|current", end, re.IGNORECASE) else int(end)
            exp_years += max(0, end - start)
        except:
            continue
    numeric_match = re.findall(r'(\d+)\+?\s+years? of experience', text, re.IGNORECASE)
    if numeric_match:
        exp_years = max(exp_years, max([int(x) for x in numeric_match]))
    return exp_years

def extract_education(text):
    edu_keywords = ['bachelor','master','phd','mba','btech','mtech']
    text = clean_text(text)
    return [kw for kw in edu_keywords if kw in text]

def sentiment_analysis(text):
    return TextBlob(text).sentiment.polarity

def parse_resume(file):
    data = {}
    text = ""
    file_bytes = file.read()
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    elif filename.endswith(".txt"):
        text = extract_text_from_txt(file_bytes)
    elif filename.endswith((".png",".jpg",".jpeg")):
        text = extract_text_from_image(file_bytes)
    else:
        return None

    data['text'] = text
    data['skills'] = extract_skills(text)
    data['experience_years'] = estimate_experience(text)
    data['education'] = extract_education(text)
    data['grammar_errors'], data['spelling_errors'] = grammar_check(text)
    data['sentiment'] = sentiment_analysis(text)

    cleaned = clean_text(text)
    pred_encoded = clf.predict([cleaned])[0]
    pred_label = le.inverse_transform([pred_encoded])[0]
    probs = clf.predict_proba([cleaned])[0]
    conf_percent = max(probs)*100
    data['predicted_role'] = pred_label
    data['pred_confidence'] = round(conf_percent,2)
    top3_idx = probs.argsort()[-3:][::-1]
    top3_labels = le.inverse_transform(top3_idx)
    top3_probs = probs[top3_idx]
    data['top3_roles'] = list(zip(top3_labels, [round(p*100,2) for p in top3_probs]))

    return data

# ---------------- Job Description ----------------
def parse_job_description(jd_text):
    jd_data = {}
    jd_text_clean = clean_text(jd_text)
    jd_data['required_skills'] = extract_skills(jd_text_clean)
    jd_data['min_experience'] = estimate_experience(jd_text_clean)
    jd_data['required_education'] = extract_education(jd_text_clean)
    return jd_data

# ---------------- ATS ----------------
def compute_match_score(resume_data, jd_data, desired_role=None):
    weight_skills = 0.5
    weight_experience = 0.3
    weight_education = 0.1
    weight_role = 0.1

    skill_score = 1.0
    if jd_data.get('required_skills'):
        matched_skills = [s for s in jd_data['required_skills'] if s in resume_data['skills']]
        skill_score = len(matched_skills)/len(jd_data['required_skills'])

    exp_score = min(resume_data.get('experience_years',0)/max(jd_data.get('min_experience',0),1),1.0)

    edu_score = 1.0
    if jd_data.get('required_education'):
        edu_score = len([e for e in resume_data.get('education',[]) if e in jd_data['required_education']])/len(jd_data['required_education'])

    role_score = 0.0
    if desired_role:
        role_score = SequenceMatcher(None, desired_role.lower(), resume_data['predicted_role'].lower()).ratio()

    final_score = (skill_score*weight_skills + exp_score*weight_experience +
                   edu_score*weight_education + role_score*weight_role) * 100
    return round(final_score,2)

# ---------------- Routes ----------------
@app.route("/", methods=["GET","POST"])
def index():
    global job_description_data
    if request.method == "POST":
        jd_text = request.form.get("jd_text")
        if jd_text:
            job_description_data = parse_job_description(jd_text)
    return render_template("index.html")

@app.route("/upload_page")
def upload_page():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_resume():
    global candidates
    desired_role = request.form.get("desired_role")
    file = request.files.get("resume_file")
    if file:
        resume_data = parse_resume(file)
        if resume_data:
            candidate_id = len(candidates)+1
            candidates.append({
                'id': candidate_id,
                'resume_data': resume_data,
                'full_text': resume_data.get('text','')
            })
            match_score = compute_match_score(resume_data, job_description_data, desired_role) if job_description_data else None
            return render_template(
                "result.html",
                candidate_id=candidate_id,
                resume=resume_data,
                match_score=match_score,
                desired_role=desired_role
            )
    return redirect(url_for("upload_page"))

@app.route("/dashboard")
def dashboard():
    candidates_with_scores = []
    for c in candidates:
        match_score = compute_match_score(c['resume_data'], job_description_data) if job_description_data else None
        candidates_with_scores.append({**c, 'match_score': match_score})
    return render_template("dashboard.html", candidates=candidates_with_scores, jd_data=job_description_data)

@app.route("/candidate/<int:candidate_id>")
def candidate_detail(candidate_id):
    candidate = next((c for c in candidates if c['id']==candidate_id), None)
    if candidate:
        text = candidate['full_text']
        resume_data = candidate['resume_data']
        cleaned = clean_text(text)
        pred_encoded = clf.predict([cleaned])[0]
        pred_label = le.inverse_transform([pred_encoded])[0]
        probs = clf.predict_proba([cleaned])[0]
        resume_data['predicted_role'] = pred_label
        resume_data['pred_confidence'] = round(max(probs)*100,2)
        match_score = compute_match_score(resume_data, job_description_data) if job_description_data else None
        return render_template(
            "result.html",
            candidate_id=candidate_id,
            resume=resume_data,
            match_score=match_score
        )
    return redirect(url_for("dashboard"))

@app.route("/analyze_more/<int:candidate_id>")
def analyze_more(candidate_id):
    candidate = next((c for c in candidates if c['id']==candidate_id), None)
    if candidate:
        text = candidate['full_text']
        resume_data = {
            'text': text,
            'skills': extract_skills(text),
            'experience_years': estimate_experience(text),
            'education': extract_education(text),
            'grammar_errors': grammar_check(text)[0],
            'spelling_errors': grammar_check(text)[1],
            'sentiment': sentiment_analysis(text)
        }
        cleaned = clean_text(text)
        pred_encoded = clf.predict([cleaned])[0]
        pred_label = le.inverse_transform([pred_encoded])[0]
        probs = clf.predict_proba([cleaned])[0]
        resume_data['predicted_role'] = pred_label
        resume_data['pred_confidence'] = round(max(probs)*100,2)
        match_score = compute_match_score(resume_data, job_description_data) if job_description_data else None
        return render_template(
            "analyze_more.html",
            candidate_id=candidate_id,
            full_text=text,
            resume=resume_data,
            match_score=match_score
        )
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
