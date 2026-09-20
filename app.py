from flask import Flask, render_template, request, send_file
import PyPDF2
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from werkzeug.utils import secure_filename


app = Flask(__name__)


# =========================================================
# FOLDERS
# =========================================================

UPLOAD_FOLDER = "resumes"
REPORT_FOLDER = "reports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORT_FOLDER"] = REPORT_FOLDER


# =========================================================
# GENUINE SKILLS DATABASE
#
# IMPORTANT:
# Only skills present in this list can be detected.
# Random resume words will NOT become skills.
# =========================================================

GENUINE_SKILLS = {

    # -----------------------------------------------------
    # PROGRAMMING LANGUAGES
    # -----------------------------------------------------

    "python",
    "java",
    "c",
    "c++",
    "c#",
    "javascript",
    "typescript",
    "php",
    "ruby",
    "kotlin",
    "swift",
    "rust",
    "golang",
    "scala",
    "r programming",

    # -----------------------------------------------------
    # WEB DEVELOPMENT
    # -----------------------------------------------------

    "html",
    "html5",
    "css",
    "css3",
    "bootstrap",
    "tailwind css",
    "react",
    "react.js",
    "angular",
    "vue.js",
    "node.js",
    "nodejs",
    "express",
    "express.js",
    "django",
    "flask",
    "fastapi",
    "spring",
    "spring boot",

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "sqlite",
    "oracle",
    "firebase",
    "redis",
    "database management",
    "database management systems",
    "dbms",

    # -----------------------------------------------------
    # DATA SCIENCE
    # -----------------------------------------------------

    "data science",
    "data analysis",
    "data analytics",
    "data visualization",
    "data mining",
    "statistics",
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "scikit-learn",
    "sklearn",
    "jupyter",
    "jupyter notebook",

    # -----------------------------------------------------
    # ARTIFICIAL INTELLIGENCE / MACHINE LEARNING
    # -----------------------------------------------------

    "artificial intelligence",
    "ai",
    "machine learning",
    "ml",
    "deep learning",
    "neural networks",
    "natural language processing",
    "nlp",
    "computer vision",
    "generative ai",
    "genai",
    "large language models",
    "llm",
    "tensorflow",
    "keras",
    "pytorch",
    "opencv",
    "hugging face",

    # -----------------------------------------------------
    # CLOUD
    # -----------------------------------------------------

    "aws",
    "amazon web services",
    "azure",
    "microsoft azure",
    "google cloud",
    "gcp",
    "cloud computing",

    # -----------------------------------------------------
    # DEVOPS
    # -----------------------------------------------------

    "docker",
    "kubernetes",
    "jenkins",
    "devops",
    "terraform",
    "ansible",
    "ci/cd",

    # -----------------------------------------------------
    # VERSION CONTROL
    # -----------------------------------------------------

    "git",
    "github",
    "gitlab",
    "bitbucket",

    # -----------------------------------------------------
    # API / SOFTWARE
    # -----------------------------------------------------

    "api",
    "rest api",
    "restful api",
    "json",
    "xml",
    "postman",
    "software development",
    "software engineering",
    "software testing",
    "unit testing",
    "debugging",
    "automation",
    "selenium",

    # -----------------------------------------------------
    # COMPUTER SCIENCE
    # -----------------------------------------------------

    "data structures",
    "algorithms",
    "object oriented programming",
    "oop",
    "dsa",
    "computer networks",
    "networking",
    "operating systems",

    # -----------------------------------------------------
    # CYBER SECURITY
    # -----------------------------------------------------

    "cybersecurity",
    "cyber security",
    "network security",
    "ethical hacking",
    "penetration testing",

    # -----------------------------------------------------
    # OFFICE / BUSINESS TOOLS
    # -----------------------------------------------------

    "microsoft excel",
    "excel",
    "microsoft word",
    "powerpoint",
    "microsoft powerpoint",
    "power bi",
    "tableau",

    # -----------------------------------------------------
    # BIOTECHNOLOGY
    # -----------------------------------------------------

    "biotechnology",
    "microbiology",
    "molecular biology",
    "cell biology",
    "genetics",
    "biochemistry",
    "bioinformatics",
    "immunology",
    "virology",
    "genomics",
    "proteomics",
    "drug discovery",
    "biomedical science",

    # -----------------------------------------------------
    # LABORATORY SKILLS
    # -----------------------------------------------------

    "pcr",
    "pcr setup",
    "polymerase chain reaction",
    "gel electrophoresis",
    "agarose gel electrophoresis",
    "electrophoresis",
    "genome extraction",
    "dna extraction",
    "rna extraction",
    "dna isolation",
    "rna isolation",
    "pipetting",
    "microscopy",
    "spectrophotometry",
    "gram staining",
    "staining",
    "aseptic technique",
    "aseptic handling",
    "sterile technique",
    "sterilization",
    "autoclaving",
    "inoculation",
    "streak plating",
    "culture media",
    "culture media preparation",
    "sample handling",
    "sample processing",
    "sample accessioning",
    "microbial testing",
    "laboratory techniques",
    "laboratory testing",
    "lab techniques",
    "lab safety",
    "biosafety",
    "bsl protocols",
    "quality control",
    "quality assurance",

    # -----------------------------------------------------
    # RESEARCH
    # -----------------------------------------------------

    "research methodology",
    "research writing",
    "scientific writing",
    "technical writing",
    "literature review",
    "literature reviews",
    "research papers",
    "research articles",
    "data interpretation",
    "experimental design",
    "documentation",

    # -----------------------------------------------------
    # BIOINFORMATICS
    # -----------------------------------------------------

    "ncbi",
    "sequence analysis",
    "genome analysis",
    "protein analysis",
    "biological databases",
    "bioinformatics tools",

    # -----------------------------------------------------
    # BUSINESS / MANAGEMENT
    # -----------------------------------------------------

    "business analysis",
    "business development",
    "project management",
    "product management",
    "operations management",
    "team management",
    "customer relationship management",
    "crm",

    # -----------------------------------------------------
    # MARKETING
    # -----------------------------------------------------

    "digital marketing",
    "social media marketing",
    "content marketing",
    "content writing",
    "seo",
    "search engine optimization",
    "sem",
    "market research",
    "brand management",
    "email marketing",
    "advertising",

    # -----------------------------------------------------
    # FINANCE / ACCOUNTING
    # -----------------------------------------------------

    "financial analysis",
    "financial management",
    "accounting",
    "bookkeeping",
    "auditing",
    "taxation",
    "budgeting",
    "financial reporting",

    # -----------------------------------------------------
    # SOFT SKILLS
    # -----------------------------------------------------

    "communication",
    "leadership",
    "teamwork",
    "problem solving",
    "critical thinking",
    "time management",
    "adaptability",
    "collaboration",
    "creativity",
    "presentation skills",
    "interpersonal skills",
    "decision making",
    "organizational skills"
}


# =========================================================
# FILE CHECK
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.lower().endswith(".pdf")
    )


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_text_from_pdf(filepath):

    text = ""

    try:

        with open(filepath, "rb") as pdf_file:

            reader = PyPDF2.PdfReader(pdf_file)

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:

                    text += page_text + "\n"

    except Exception as error:

        print("PDF extraction error:", error)

    return text


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text):

    text = text.lower()

    # Different dash characters
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# STRICT GENUINE SKILL DETECTION
# =========================================================

def detect_skills(text):

    normalized_text = normalize_text(text)

    detected = []

    # -----------------------------------------------------
    # LONGEST SKILLS FIRST
    #
    # Example:
    # "gel electrophoresis" is checked before
    # "electrophoresis"
    # -----------------------------------------------------

    sorted_skills = sorted(
        GENUINE_SKILLS,
        key=len,
        reverse=True
    )

    for skill in sorted_skills:

        skill_lower = skill.lower().strip()

        # Escape regex characters
        pattern = re.escape(
            skill_lower
        )

        # Allow multiple spaces between words
        pattern = pattern.replace(
            r"\ ",
            r"\s+"
        )

        # Exact word / phrase boundary
        regex = (
            r"(?<![a-zA-Z0-9])"
            + pattern
            + r"(?![a-zA-Z0-9])"
        )

        if re.search(
            regex,
            normalized_text,
            flags=re.IGNORECASE
        ):

            detected.append(
                skill
            )

    # -----------------------------------------------------
    # REMOVE DUPLICATES
    # -----------------------------------------------------

    unique_skills = []

    seen = set()

    for skill in detected:

        key = skill.lower()

        if key not in seen:

            seen.add(key)

            unique_skills.append(
                skill
            )

    # -----------------------------------------------------
    # REMOVE SHORTER DUPLICATE CONCEPTS
    #
    # Example:
    # If "gel electrophoresis" exists,
    # "electrophoresis" is not separately displayed.
    # -----------------------------------------------------

    final_skills = []

    for skill in unique_skills:

        skill_lower = skill.lower()

        is_part_of_longer_skill = False

        for other in unique_skills:

            other_lower = other.lower()

            if (
                skill_lower != other_lower
                and skill_lower in other_lower
                and len(other_lower) > len(skill_lower)
            ):

                is_part_of_longer_skill = True

                break

        if not is_part_of_longer_skill:

            final_skills.append(
                skill
            )

    # -----------------------------------------------------
    # C vs C++
    # -----------------------------------------------------

    has_cpp = any(
        skill.lower() == "c++"
        for skill in final_skills
    )

    if has_cpp:

        final_skills = [
            skill
            for skill in final_skills
            if skill.lower() != "c"
        ]

    # -----------------------------------------------------
    # SORT ALPHABETICALLY
    # -----------------------------------------------------

    final_skills.sort(
        key=str.lower
    )

    return final_skills


# =========================================================
# RESUME SCORE
# =========================================================

def calculate_resume_score(
    text,
    skills
):

    normalized_text = normalize_text(text)

    score = 0

    # -----------------------------------------------------
    # CONTACT INFORMATION - 15
    # -----------------------------------------------------

    if "@" in normalized_text:

        score += 8

    if re.search(
        r"\b\d{10}\b",
        normalized_text
    ):

        score += 7

    # -----------------------------------------------------
    # EDUCATION - 15
    # -----------------------------------------------------

    education_keywords = [
        "education",
        "b.tech",
        "btech",
        "bachelor",
        "master",
        "degree",
        "university",
        "college",
        "school",
        "b.sc",
        "m.sc",
        "mba",
        "bca",
        "mca",
        "graduation"
    ]

    if any(
        keyword in normalized_text
        for keyword in education_keywords
    ):

        score += 15

    # -----------------------------------------------------
    # SKILLS - 20
    # -----------------------------------------------------

    skill_count = len(skills)

    if skill_count >= 10:

        score += 20

    elif skill_count >= 7:

        score += 16

    elif skill_count >= 5:

        score += 12

    elif skill_count >= 3:

        score += 8

    elif skill_count >= 1:

        score += 4

    # -----------------------------------------------------
    # EXPERIENCE - 15
    # -----------------------------------------------------

    experience_keywords = [
        "experience",
        "internship",
        "intern",
        "worked",
        "employment",
        "professional experience"
    ]

    if any(
        keyword in normalized_text
        for keyword in experience_keywords
    ):

        score += 15

    # -----------------------------------------------------
    # PROJECTS - 15
    # -----------------------------------------------------

    project_keywords = [
        "project",
        "projects",
        "developed",
        "built",
        "application",
        "website"
    ]

    if any(
        keyword in normalized_text
        for keyword in project_keywords
    ):

        score += 15

    # -----------------------------------------------------
    # CERTIFICATIONS - 10
    # -----------------------------------------------------

    certification_keywords = [
        "certification",
        "certificate",
        "certified",
        "course",
        "training",
        "workshop"
    ]

    if any(
        keyword in normalized_text
        for keyword in certification_keywords
    ):

        score += 10

    # -----------------------------------------------------
    # LINKEDIN - 5
    # -----------------------------------------------------

    if "linkedin" in normalized_text:

        score += 5

    # -----------------------------------------------------
    # GITHUB - 5
    # -----------------------------------------------------

    if "github" in normalized_text:

        score += 5

    return min(
        score,
        100
    )


# =========================================================
# RESUME SECTION ANALYSIS
# =========================================================

def analyze_sections(text):

    normalized_text = normalize_text(text)

    analysis = {}

    # -----------------------------------------------------
    # CONTACT
    # -----------------------------------------------------

    analysis["Contact Information"] = (

        "Present"

        if (
            "@" in normalized_text
            or re.search(
                r"\b\d{10}\b",
                normalized_text
            )
        )

        else "Missing"
    )

    # -----------------------------------------------------
    # EDUCATION
    # -----------------------------------------------------

    education_keywords = [
        "education",
        "b.tech",
        "btech",
        "bachelor",
        "master",
        "degree",
        "university",
        "college",
        "graduation"
    ]

    analysis["Education"] = (

        "Present"

        if any(
            keyword in normalized_text
            for keyword in education_keywords
        )

        else "Missing"
    )

    # -----------------------------------------------------
    # EXPERIENCE
    # -----------------------------------------------------

    experience_keywords = [
        "experience",
        "internship",
        "intern",
        "employment",
        "worked"
    ]

    analysis["Experience"] = (

        "Present"

        if any(
            keyword in normalized_text
            for keyword in experience_keywords
        )

        else "Missing"
    )

    # -----------------------------------------------------
    # SKILLS
    # -----------------------------------------------------

    detected_skills = detect_skills(
        text
    )

    analysis["Skills"] = (

        "Present"

        if detected_skills

        else "Missing"
    )

    # -----------------------------------------------------
    # PROJECTS
    # -----------------------------------------------------

    project_keywords = [
        "project",
        "projects",
        "developed",
        "built"
    ]

    analysis["Projects"] = (

        "Present"

        if any(
            keyword in normalized_text
            for keyword in project_keywords
        )

        else "Missing"
    )

    # -----------------------------------------------------
    # CERTIFICATIONS
    # -----------------------------------------------------

    certification_keywords = [
        "certification",
        "certificate",
        "certified",
        "course",
        "training",
        "workshop"
    ]

    analysis["Certifications"] = (

        "Present"

        if any(
            keyword in normalized_text
            for keyword in certification_keywords
        )

        else "Missing"
    )

    # -----------------------------------------------------
    # LINKEDIN
    # -----------------------------------------------------

    analysis["LinkedIn"] = (

        "Present"

        if "linkedin" in normalized_text

        else "Missing"
    )

    # -----------------------------------------------------
    # GITHUB
    # -----------------------------------------------------

    analysis["GitHub"] = (

        "Present"

        if "github" in normalized_text

        else "Missing"
    )

    return analysis


# =========================================================
# JOB DESCRIPTION MATCHING
# =========================================================

def analyze_job_description(
    resume_text,
    job_description
):

    resume_skills = detect_skills(
        resume_text
    )

    required_skills = detect_skills(
        job_description
    )

    resume_lower = {
        skill.lower()
        for skill in resume_skills
    }

    matched_skills = []

    missing_skills = []

    for skill in required_skills:

        if skill.lower() in resume_lower:

            matched_skills.append(
                skill
            )

        else:

            missing_skills.append(
                skill
            )

    if required_skills:

        match_percentage = round(
            (
                len(matched_skills)
                /
                len(required_skills)
            )
            * 100
        )

    else:

        match_percentage = 0

    return {
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_percentage": match_percentage
    }


# =========================================================
# IMPROVEMENT SUGGESTIONS
# =========================================================

def generate_suggestions(
    text,
    skills,
    section_analysis,
    job_analysis
):

    suggestions = []

    normalized_text = normalize_text(
        text
    )

    # -----------------------------------------------------
    # PROJECTS
    # -----------------------------------------------------

    if section_analysis.get(
        "Projects"
    ) == "Missing":

        suggestions.append(
            "Add 2-3 relevant academic or personal "
            "projects with a short description of "
            "your contribution."
        )

    # -----------------------------------------------------
    # GITHUB
    # -----------------------------------------------------

    if section_analysis.get(
        "GitHub"
    ) == "Missing":

        suggestions.append(
            "Add your GitHub profile link to showcase "
            "your projects and practical work."
        )

    # -----------------------------------------------------
    # LINKEDIN
    # -----------------------------------------------------

    if section_analysis.get(
        "LinkedIn"
    ) == "Missing":

        suggestions.append(
            "Add your LinkedIn profile link to make "
            "your professional profile easier to find."
        )

    # -----------------------------------------------------
    # CERTIFICATIONS
    # -----------------------------------------------------

    if section_analysis.get(
        "Certifications"
    ) == "Missing":

        suggestions.append(
            "Add relevant certifications, courses or "
            "workshops related to your target field."
        )

    # -----------------------------------------------------
    # EXPERIENCE
    # -----------------------------------------------------

    if section_analysis.get(
        "Experience"
    ) == "Missing":

        suggestions.append(
            "Add internship, training, freelance or "
            "relevant practical experience if available."
        )

    # -----------------------------------------------------
    # EDUCATION
    # -----------------------------------------------------

    if section_analysis.get(
        "Education"
    ) == "Missing":

        suggestions.append(
            "Add a clear Education section with your "
            "degree, college/university and graduation year."
        )

    # -----------------------------------------------------
    # CONTACT
    # -----------------------------------------------------

    if section_analysis.get(
        "Contact Information"
    ) == "Missing":

        suggestions.append(
            "Add professional contact information "
            "such as email address and phone number."
        )

    # -----------------------------------------------------
    # SKILLS
    # -----------------------------------------------------

    if len(skills) < 5:

        suggestions.append(
            "Add more relevant skills from your field "
            "to clearly show your expertise."
        )

    # -----------------------------------------------------
    # JOB DESCRIPTION
    # -----------------------------------------------------

    if job_analysis:

        missing = job_analysis.get(
            "missing_skills",
            []
        )

        if missing:

            suggestions.append(
                "Consider learning or improving these "
                "job-required skills: "
                + ", ".join(missing)
                + "."
            )

        if job_analysis.get(
            "match_percentage",
            0
        ) < 50:

            suggestions.append(
                "Your resume has a relatively low skill "
                "match with the provided job description. "
                "Add relevant skills and projects where "
                "they genuinely apply."
            )

    # -----------------------------------------------------
    # SHORT RESUME
    # -----------------------------------------------------

    if len(normalized_text) < 500:

        suggestions.append(
            "Your resume contains limited text. "
            "Consider adding more details about projects, "
            "experience, skills and achievements."
        )

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    if not suggestions:

        suggestions.append(
            "Your resume contains the major sections "
            "detected by the analyzer. Keep the content "
            "concise and tailored to the target job."
        )

    return suggestions


# =========================================================
# CREATE PDF REPORT
# =========================================================

def create_pdf_report(
    filename,
    resume_score,
    detected_skills,
    section_analysis,
    job_analysis,
    suggestions
):

    report_path = os.path.join(
        app.config["REPORT_FOLDER"],
        filename
    )

    pdf = canvas.Canvas(
        report_path,
        pagesize=A4
    )

    width, height = A4

    x = 50
    y = height - 50

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        20
    )

    pdf.drawString(
        x,
        y,
        "AI Resume Analyzer - Analysis Report"
    )

    y -= 35

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        x,
        y,
        "Automatically generated resume analysis report"
    )

    y -= 40

    # -----------------------------------------------------
    # SCORE
    # -----------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        15
    )

    pdf.drawString(
        x,
        y,
        "Resume Score"
    )

    y -= 25

    pdf.setFont(
        "Helvetica-Bold",
        24
    )

    pdf.drawString(
        x,
        y,
        f"{resume_score} / 100"
    )

    y -= 40

    # -----------------------------------------------------
    # JOB MATCH
    # -----------------------------------------------------

    if job_analysis:

        pdf.setFont(
            "Helvetica-Bold",
            15
        )

        pdf.drawString(
            x,
            y,
            "Job Description Match"
        )

        y -= 25

        pdf.setFont(
            "Helvetica-Bold",
            18
        )

        pdf.drawString(
            x,
            y,
            f"{job_analysis.get('match_percentage', 0)}%"
        )

        y -= 35

    # -----------------------------------------------------
    # DETECTED SKILLS
    # -----------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        15
    )

    pdf.drawString(
        x,
        y,
        "Detected Skills"
    )

    y -= 22

    pdf.setFont(
        "Helvetica",
        10
    )

    skills_text = ", ".join(
        detected_skills
    )

    if not skills_text:

        skills_text = "No recognized skills detected."

    # Wrap skills
    words = skills_text.split()

    line = ""

    for word in words:

        test_line = line + word + " "

        if pdf.stringWidth(
            test_line,
            "Helvetica",
            10
        ) > 500:

            pdf.drawString(
                x,
                y,
                line
            )

            y -= 15

            line = word + " "

        else:

            line = test_line

    if line:

        pdf.drawString(
            x,
            y,
            line
        )

        y -= 30

    # -----------------------------------------------------
    # SECTION ANALYSIS
    # -----------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        15
    )

    pdf.drawString(
        x,
        y,
        "Resume Section Analysis"
    )

    y -= 22

    pdf.setFont(
        "Helvetica",
        10
    )

    for section, status in section_analysis.items():

        pdf.drawString(
            x,
            y,
            f"{section}: {status}"
        )

        y -= 16

        if y < 70:

            pdf.showPage()

            y = height - 50

            pdf.setFont(
                "Helvetica",
                10
            )

    y -= 10

    # -----------------------------------------------------
    # MATCHED / MISSING SKILLS
    # -----------------------------------------------------

    if job_analysis:

        pdf.setFont(
            "Helvetica-Bold",
            15
        )

        pdf.drawString(
            x,
            y,
            "Matched Skills"
        )

        y -= 22

        pdf.setFont(
            "Helvetica",
            10
        )

        matched = job_analysis.get(
            "matched_skills",
            []
        )

        matched_text = ", ".join(
            matched
        )

        if not matched_text:

            matched_text = "None"

        pdf.drawString(
            x,
            y,
            matched_text[:90]
        )

        y -= 25

        pdf.setFont(
            "Helvetica-Bold",
            15
        )

        pdf.drawString(
            x,
            y,
            "Missing Skills"
        )

        y -= 22

        pdf.setFont(
            "Helvetica",
            10
        )

        missing = job_analysis.get(
            "missing_skills",
            []
        )

        missing_text = ", ".join(
            missing
        )

        if not missing_text:

            missing_text = "None"

        pdf.drawString(
            x,
            y,
            missing_text[:90]
        )

        y -= 30

    # -----------------------------------------------------
    # SUGGESTIONS
    # -----------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        15
    )

    pdf.drawString(
        x,
        y,
        "Resume Improvement Suggestions"
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        10
    )

    for suggestion in suggestions:

        words = suggestion.split()

        line = "• "

        for word in words:

            test_line = line + word + " "

            if pdf.stringWidth(
                test_line,
                "Helvetica",
                10
            ) > 500:

                pdf.drawString(
                    x,
                    y,
                    line
                )

                y -= 15

                line = "  " + word + " "

            else:

                line = test_line

        if line.strip():

            pdf.drawString(
                x,
                y,
                line
            )

            y -= 20

        if y < 60:

            pdf.showPage()

            y = height - 50

            pdf.setFont(
                "Helvetica",
                10
            )

    pdf.setFont(
        "Helvetica-Oblique",
        8
    )

    pdf.drawString(
        x,
        30,
        "AI Resume Analyzer"
    )

    pdf.save()

    return report_path


# =========================================================
# MAIN PAGE
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    message = None
    extracted_text = None
    detected_skills = []
    resume_score = None
    section_analysis = {}
    job_description = ""
    job_analysis = None
    suggestions = []
    report_filename = None

    # =====================================================
    # POST REQUEST
    # =====================================================

    if request.method == "POST":

        file = request.files.get(
            "file"
        )

        job_description = request.form.get(
            "job_description",
            ""
        ).strip()

        # -------------------------------------------------
        # FILE CHECK
        # -------------------------------------------------

        if not file:

            message = "Please select a PDF resume."

            return render_template(
                "index.html",
                message=message,
                extracted_text=extracted_text,
                detected_skills=detected_skills,
                resume_score=resume_score,
                section_analysis=section_analysis,
                job_description=job_description,
                job_analysis=job_analysis,
                suggestions=suggestions,
                report_filename=report_filename
            )

        if not file.filename:

            message = "Please select a PDF resume."

            return render_template(
                "index.html",
                message=message,
                extracted_text=extracted_text,
                detected_skills=detected_skills,
                resume_score=resume_score,
                section_analysis=section_analysis,
                job_description=job_description,
                job_analysis=job_analysis,
                suggestions=suggestions,
                report_filename=report_filename
            )

        if not allowed_file(
            file.filename
        ):

            message = "Only PDF files are allowed."

            return render_template(
                "index.html",
                message=message,
                extracted_text=extracted_text,
                detected_skills=detected_skills,
                resume_score=resume_score,
                section_analysis=section_analysis,
                job_description=job_description,
                job_analysis=job_analysis,
                suggestions=suggestions,
                report_filename=report_filename
            )

        # -------------------------------------------------
        # SAVE RESUME
        # -------------------------------------------------

        filename = secure_filename(
            file.filename
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        file.save(
            filepath
        )

        # -------------------------------------------------
        # EXTRACT TEXT
        # -------------------------------------------------

        extracted_text = extract_text_from_pdf(
            filepath
        )

        if not extracted_text.strip():

            message = (
                "Could not extract text from this PDF. "
                "Please upload a text-based PDF."
            )

            return render_template(
                "index.html",
                message=message,
                extracted_text=extracted_text,
                detected_skills=detected_skills,
                resume_score=resume_score,
                section_analysis=section_analysis,
                job_description=job_description,
                job_analysis=job_analysis,
                suggestions=suggestions,
                report_filename=report_filename
            )

        # -------------------------------------------------
        # DETECT GENUINE SKILLS
        # -------------------------------------------------

        detected_skills = detect_skills(
            extracted_text
        )

        # -------------------------------------------------
        # SCORE
        # -------------------------------------------------

        resume_score = calculate_resume_score(
            extracted_text,
            detected_skills
        )

        # -------------------------------------------------
        # SECTION ANALYSIS
        # -------------------------------------------------

        section_analysis = analyze_sections(
            extracted_text
        )

        # -------------------------------------------------
        # JOB DESCRIPTION
        # -------------------------------------------------

        if job_description:

            job_analysis = analyze_job_description(
                extracted_text,
                job_description
            )

        # -------------------------------------------------
        # SUGGESTIONS
        # -------------------------------------------------

        suggestions = generate_suggestions(
            extracted_text,
            detected_skills,
            section_analysis,
            job_analysis
        )

        # -------------------------------------------------
        # CREATE PDF REPORT
        # -------------------------------------------------

        report_filename = "resume_analysis_report.pdf"

        create_pdf_report(
            report_filename,
            resume_score,
            detected_skills,
            section_analysis,
            job_analysis,
            suggestions
        )

        message = "Resume analyzed successfully!"

    # =====================================================
    # RENDER PAGE
    # =====================================================

    return render_template(
        "index.html",
        message=message,
        extracted_text=extracted_text,
        detected_skills=detected_skills,
        resume_score=resume_score,
        section_analysis=section_analysis,
        job_description=job_description,
        job_analysis=job_analysis,
        suggestions=suggestions,
        report_filename=report_filename
    )


# =========================================================
# DOWNLOAD ANALYSIS REPORT
# =========================================================

@app.route(
    "/download-report/<filename>"
)
def download_report(filename):

    filename = secure_filename(
        filename
    )

    report_path = os.path.join(
        app.config["REPORT_FOLDER"],
        filename
    )

    if not os.path.exists(
        report_path
    ):

        return "Report not found.", 404

    return send_file(
        report_path,
        as_attachment=True,
        download_name="AI_Resume_Analysis_Report.pdf"
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )