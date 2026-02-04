import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

STOPWORDS = {
    "a","an","the","and","or","in","on","with","to","for","of","by",
    "is","are","was","were","this","that","it","as","at","from",
    "be","have","has","had","i","we","you","they","their"
}

def normalize_text(text):
    text = text.lower()
    for k, v in SKILL_MAP.items():
        text = text.replace(k, v)
    return text

def _tokens(text):
    return [
        w for w in re.findall(r"\w+", text.lower())
        if w not in STOPWORDS and len(w) > 2
    ]

# 🔥 THIS FUNCTION NAME MUST MATCH
def analyze_resume(resume, jd):
    if not resume or not jd:
        return {
            "overall_score": 0,
            "breakdown": {
                "skills": 0,
                "projects": 0,
                "education": 0,
                "keywords": 0
            },
            "missing_keywords": []
        }

    resume_n = normalize_text(resume)
    jd_n = normalize_text(jd)

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        vectors = vectorizer.fit_transform([resume_n, jd_n])
        similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
    except ValueError:
        similarity = 0

    score = round(similarity * 100, 2)
    missing = list(set(_tokens(jd_n)) - set(_tokens(resume_n)))[:10]

    return {
        "overall_score": score,
        "breakdown": {
            "skills": round(score * 0.35, 2),
            "projects": round(score * 0.30, 2),
            "education": round(score * 0.15, 2),
            "keywords": round(score * 0.20, 2)
        },
        "missing_keywords": missing
    }
