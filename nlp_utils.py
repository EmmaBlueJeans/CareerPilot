import re

SKILL_PATTERNS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r",
    "sql", "postgresql", "mysql", "sqlite", "mongodb", "redis", "bigquery",
    "pandas", "numpy", "matplotlib", "seaborn", "scikit-learn", "tensorflow",
    "pytorch", "keras", "spacy", "nltk",
    "machine learning", "deep learning", "nlp", "computer vision",
    "data analysis", "data analytics", "data visualization", "data visualisation",
    "data cleaning", "data wrangling", "etl", "elt", "data pipeline",
    "data pipelines", "statistics", "reporting",
    "tableau", "power bi", "powerbi", "looker", "lookml", "excel",
    "business intelligence", "bi", "dashboard", "dashboards",
    "react", "vue", "angular", "next.js", "node.js", "express",
    "flask", "django", "fastapi", "spring", "rails",
    "html", "css", "tailwind", "bootstrap",
    "aws", "azure", "google cloud", "gcp", "docker", "kubernetes",
    "terraform", "ansible", "ci/cd", "github actions", "jenkins",
    "git", "github", "gitlab",
    "rest", "graphql", "api", "apis", "microservices",
    "linux", "unix", "bash", "shell scripting",
    "agile", "scrum", "jira",
    "communication", "stakeholder management", "presentation",
    "presentations", "presenting", "presented", "problem solving",
    "leadership", "teamwork", "automation", "testing", "unit testing",
    "tcp/ip", "ethernet", "networking", "embedded systems", "sdk", "bsp",
    "dpdk", "firmware", "debugging",
]

NORMALIZE_SKILL = {
    "powerbi": "power bi",
    "postgresql": "sql",
    "mysql": "sql",
    "sqlite": "sql",
    "dashboards": "dashboard",
    "data analytics": "data analysis",
    "data visualisation": "data visualization",
    "apis": "api",
    "presentations": "presentation",
    "presenting": "presentation",
    "presented": "presentation",
    "data pipelines": "data pipeline",
    "looker": "business intelligence",
    "lookml": "business intelligence",
    "bi": "business intelligence",
    "gcp": "google cloud",
    "node.js": "node",
    "next.js": "next",
}

SKILL_WEIGHTS = {
    "python": 3, "sql": 3, "data analysis": 3, "data visualization": 3,
    "machine learning": 3, "business intelligence": 3, "java": 3,
    "javascript": 3, "typescript": 3, "react": 3, "deep learning": 3,
    "nlp": 3, "linux": 3, "embedded systems": 3,
    "power bi": 2, "tableau": 2, "excel": 2, "statistics": 2,
    "reporting": 2, "dashboard": 2, "etl": 2, "data pipeline": 2,
    "bigquery": 2, "aws": 2, "azure": 2, "google cloud": 2, "api": 2,
    "docker": 2, "kubernetes": 2, "flask": 2, "django": 2, "fastapi": 2,
    "node": 2, "networking": 2, "firmware": 2, "sdk": 2, "bsp": 2,
}

_spacy_pipeline = None


def _load_spacy():
    global _spacy_pipeline
    if _spacy_pipeline is not None:
        return _spacy_pipeline
    try:
        import spacy
        from spacy.matcher import PhraseMatcher

        nlp = spacy.load("en_core_web_sm")
        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        patterns = [nlp.make_doc(skill) for skill in SKILL_PATTERNS]
        matcher.add("SKILLS", patterns)
        _spacy_pipeline = (nlp, matcher)
    except Exception:
        _spacy_pipeline = False
    return _spacy_pipeline


def extract_skills(text):
    if not text:
        return []
    text = re.sub(r"\s+", " ", text).strip()

    pipeline = _load_spacy()
    skills = set()

    if pipeline:
        nlp, matcher = pipeline
        doc = nlp(text)
        for _, start, end in matcher(doc):
            skill = doc[start:end].text.lower().strip()
            skills.add(NORMALIZE_SKILL.get(skill, skill))
    else:
        lowered = text.lower()
        for skill in SKILL_PATTERNS:
            pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
            if re.search(pattern, lowered):
                skills.add(NORMALIZE_SKILL.get(skill, skill))

    return sorted(skills)


def compare_skills(resume_skills, job_skills):
    resume_set = {s.lower() for s in resume_skills if s}
    job_set = {s.lower() for s in job_skills if s}

    matched = sorted(resume_set & job_set)
    missing = sorted(job_set - resume_set)

    total_weight = sum(SKILL_WEIGHTS.get(s, 1) for s in job_set)
    matched_weight = sum(SKILL_WEIGHTS.get(s, 1) for s in matched)

    score = 0 if total_weight == 0 else round((matched_weight / total_weight) * 100)

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
    }
