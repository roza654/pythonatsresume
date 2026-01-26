from flask import Flask, render_template, request, jsonify
from docx import Document
import pdfplumber
import re
import io
import os

# 🔥 SMART ATS (ML)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ================= FLASK APP =================
app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTS = (".pdf", ".docx")

# ================= LINKEDIN HELPERS =================
def _ensure_protocol(url):
    if not url:
        return ""
    return url if url.lower().startswith(("http://", "https://")) else "https://" + url

def extract_linkedin(text, lines, email):
    match = re.search(
        r"(https?:\/\/)?(www\.)?linkedin\.com\/[A-Za-z0-9\-\._\/]+",
        text, re.IGNORECASE
    )
    if match:
        return _ensure_protocol(match.group(0))

    for i, line in enumerate(lines):
        if "linkedin" in line.lower():
            m = re.search(
                r"(https?:\/\/)?(www\.)?linkedin\.com\/[A-Za-z0-9\-\._\/]+",
                line, re.IGNORECASE
            )
            if m:
                return _ensure_protocol(m.group(0))

            if i + 1 < len(lines):
                m = re.search(
                    r"(https?:\/\/)?(www\.)?linkedin\.com\/[A-Za-z0-9\-\._\/]+",
                    lines[i + 1], re.IGNORECASE
                )
                if m:
                    return _ensure_protocol(m.group(0))

    if email:
        username = email.split("@")[0]
        return f"https://linkedin.com/in/{username}"

    return ""

# ================= SMART ATS HELPERS =================
SKILL_MAP = {
    "mysql": "sql",
    "postgresql": "sql",
    "sqlite": "sql",
    "javascript": "js",
    "reactjs": "react",
    "nodejs": "node",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "rest api": "api"
}

def normalize_text(text):
    text = text.lower()
    for k, v in SKILL_MAP.items():
        text = text.replace(k, v)
    return text

STOPWORDS = {
    "a","an","the","and","or","in","on","with","to","for","of","by","is","are","was","were",
    "this","that","it","as","at","from","be","have","has","had","i","we","you","they","their"
}

def _tokens(s):
    return [w for w in re.findall(r"\w+", s.lower()) if w not in STOPWORDS]

# ================= ROUTES =================
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/build-resume")
def build_resume():
    return render_template("index.html")

# ================= RESUME EXTRACTION =================
@app.route("/extract_resume", methods=["POST"])
def extract_resume():
    try:
        file = request.files.get("resume")
        if not file:
            return jsonify({"error": "no file uploaded"}), 400

        filename = file.filename.lower()
        if not filename.endswith(ALLOWED_EXTS):
            return jsonify({"error": "unsupported file type"}), 400

        file_bytes = file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            return jsonify({"error": "file too large"}), 413

        text = ""

        # ---------- TEXT EXTRACTION ----------
        if filename.endswith(".docx"):
            doc = Document(io.BytesIO(file_bytes))
            parts = []

            for p in doc.paragraphs:
                if p.text.strip():
                    parts.append(p.text.strip())

            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            parts.append(cell.text.strip())

            text = "\n".join(parts)

        elif filename.endswith(".pdf"):
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
                text = "\n".join(pages)

        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # ---------- EMAIL ----------
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        email = email_match.group(0) if email_match else ""

        # ---------- PHONE ----------
        phone_match = re.search(r"(\+\d{1,3}[-\s]?)?\d{7,15}", text)
        phone = phone_match.group(0) if phone_match else ""

        # ---------- LINKEDIN ----------
        linkedin = extract_linkedin(text, lines, email)

        # ---------- LOCATION ----------
        location = ""
        for line in lines:
            if "location" in line.lower() or "address" in line.lower():
                location = line.split(":")[-1].strip()
                break

        # ---------- FULL NAME (ROBUST ATS LOGIC) ----------
        full_name = ""

        bad_words = [
            "intern","developer","engineer","company","solutions","pvt","ltd",
            "web","software","career","objective","summary","profile",
            "education","skills","experience","resume","artificial","intelligence","data","science"
        ]

        def is_valid_name(line):
            words = line.split()
            return (
                2 <= len(words) <= 3 and
                not any(bw in line.lower() for bw in bad_words) and
                not any(char.isdigit() for char in line)
            )

        # Priority 1: top of resume
        for line in lines[:5]:
            if is_valid_name(line):
                full_name = line
                break

        # Priority 2: near email
        if not full_name and email:
            for i, line in enumerate(lines):
                if email in line:
                    for j in range(max(0, i - 3), i):
                        if is_valid_name(lines[j]):
                            full_name = lines[j]
                            break
                    break

        # Fallback
        if not full_name:
            for line in lines[:10]:
                if is_valid_name(line):
                    full_name = line
                    break

        # ---------- PROJECTS ----------
        projects = []
        capture = False

        for line in lines:
            l = line.lower()
            if "project" in l:
                capture = True
                continue

            if capture and any(x in l for x in [
                "education","skills","experience","internship",
                "certification","summary","objective"
            ]):
                break

            if capture and len(line) > 5:
                projects.append(line)

        # ---------- SKILLS ----------
        skills_list = [
            "python","c","c++","java","flask","django",
            "html","css","javascript","sql","mysql","react","node"
        ]
        found_skills = [s for s in skills_list if re.search(rf"\b{s}\b", text.lower())]

        return jsonify({
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "location": location,
            "linkedin": linkedin,
            "skills": ", ".join(found_skills),
            "projects": "\n".join(projects),
            "summary": text[:900] + "..." if len(text) > 900 else text
        })

    except Exception as e:
        return jsonify({"error": "failed to parse resume", "details": str(e)}), 400

# ================= SMART ATS ANALYSIS =================
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json or {}
    resume = data.get("resume", "")
    jd = data.get("job_description", "")

    if not resume or not jd:
        return jsonify({"score": 0, "missing_keywords": []})

    resume_n = normalize_text(resume)
    jd_n = normalize_text(jd)

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume_n, jd_n])
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]

    score = round(similarity * 100, 2)
    missing = list(set(_tokens(jd_n)) - set(_tokens(resume_n)))[:8]
    return jsonify({
    "overall_score": score,
    "breakdown": {
        "skills": round(score * 0.35, 2),
        "projects": round(score * 0.30, 2),
        "education": round(score * 0.15, 2),
        "keywords": round(score * 0.20, 2)
    },
    "missing_keywords": missing
})

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
