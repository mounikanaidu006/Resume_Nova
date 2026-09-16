import re
from collections import Counter
import fitz


# =========================================================
# GENERIC LANGUAGE FILTERS
# =========================================================

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "to", "of",
    "in", "on", "for", "with", "as", "at", "by", "from",
    "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its",
    "we", "you", "your", "our", "their", "they", "them",
    "he", "she", "his", "her", "will", "would", "should",
    "can", "could", "may", "might", "must", "have", "has",
    "had", "do", "does", "did", "about", "into", "through",
    "during", "before", "after", "above", "below", "up",
    "down", "out", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "who", "what", "which", "while"
}


# Generic job-ad wording.
# These words should not become individual job requirements.

JD_FILLER_WORDS = {
    "candidate", "candidates",
    "role", "position", "job",
    "required", "requires", "require", "requiring",
    "preferred", "preferably",
    "looking", "seek", "seeking",
    "responsibilities", "responsibility",
    "requirements", "requirement",
    "including", "include", "includes",
    "knowledge", "experience",
    "strong", "good", "excellent",
    "ability", "abilities",
    "skills", "skill",
    "company", "organization", "organisation",
    "years", "year",
    "work", "working",
    "using", "use", "used",
    "general", "basic",
    "daily", "various",
    "appropriate", "relevant",
    "responsible",
    "support", "supporting",
    "assist", "assisting",
    "help", "helping",
    "accurate", "accuracy",
    "prepare", "preparing",
    "maintain", "maintaining",
    "activities", "activity",
    "able",
    "ensure", "ensuring",
    "understand", "understanding",
    "involve", "involves", "involving",
    "advantage",
    "familiarity",
    "comfortable",
    "effectively"
}


# Generic verbs that normally describe a responsibility,
# but by themselves are not a professional competency.

GENERIC_JD_VERBS = {
    "develop", "developing",
    "design", "designing",
    "create", "creating",
    "write", "writing",
    "review", "reviewing",
    "check", "checking",
    "update", "updating",
    "identify", "identifying",
    "execute", "executing",
    "perform", "performing",
    "fix", "fixing",
    "build", "building",
    "manage", "managing",
    "handle", "handling",
    "provide", "providing",
    "collaborate", "collaborating",
    "coordinate", "coordinating",
    "document", "documenting"
}


# =========================================================
# RESUME SECTIONS
# =========================================================

SECTION_PATTERNS = {
    "Summary / Objective": [
        "summary",
        "professional summary",
        "career objective",
        "objective",
        "profile",
        "professional profile"
    ],

    "Education": [
        "education",
        "academic qualification",
        "academic qualifications",
        "educational qualification",
        "academics"
    ],

    "Experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "employment",
        "internship",
        "internships"
    ],

    "Projects": [
        "projects",
        "project experience",
        "academic projects",
        "personal projects"
    ],

    "Skills": [
        "skills",
        "technical skills",
        "professional skills",
        "core competencies",
        "competencies",
        "key skills"
    ],

    "Certifications": [
        "certifications",
        "certification",
        "certificates",
        "professional certifications"
    ],

    "Achievements": [
        "achievements",
        "achievement",
        "awards",
        "accomplishments",
        "honors",
        "honours"
    ],

    "Languages": [
        "languages",
        "language proficiency",
        "known languages"
    ]
}


# =========================================================
# ACTION VERBS
# =========================================================

ACTION_VERBS = {
    "achieved",
    "administered",
    "analyzed",
    "analysed",
    "assisted",
    "built",
    "collaborated",
    "communicated",
    "conducted",
    "coordinated",
    "created",
    "delivered",
    "designed",
    "developed",
    "directed",
    "evaluated",
    "executed",
    "generated",
    "handled",
    "implemented",
    "improved",
    "increased",
    "led",
    "maintained",
    "managed",
    "monitored",
    "organized",
    "organised",
    "optimized",
    "performed",
    "planned",
    "prepared",
    "presented",
    "processed",
    "produced",
    "reduced",
    "researched",
    "resolved",
    "supported",
    "trained"
}


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = text.replace("\x00", " ")

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize(text):

    if not text:
        return ""

    text = text.lower()

    text = text.replace("&", " and ")

    text = re.sub(
        r"[^a-z0-9+#./\-\s]",
        " ",
        text
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================================================
# WORD NORMALIZATION
# =========================================================

def normalize_word(word):
    """
    Lightweight deterministic normalization.

    This is intentionally conservative.
    It helps common variants match without pretending
    that unrelated words mean the same thing.
    """

    word = word.lower().strip(".,:;()[]{}")

    special = {
        "analysed": "analyze",
        "analyzed": "analyze",
        "analysis": "analysis",
        "analytical": "analytical",

        "databases": "database",
        "applications": "application",
        "developers": "developer",
        "employees": "employee",
        "interviews": "interview",
        "algorithms": "algorithm",
        "structures": "structure",
        "services": "service",
        "systems": "system",
        "records": "record",
        "reports": "report",
        "scenarios": "scenario",
        "defects": "defect",
        "bugs": "bug",
        "cases": "case",
        "tests": "test",
        "apis": "api"
    }

    if word in special:
        return special[word]

    if len(word) > 5 and word.endswith("ies"):
        return word[:-3] + "y"

    if len(word) > 5 and word.endswith("ing"):
        base = word[:-3]

        if len(base) >= 4:
            return base

    if len(word) > 4 and word.endswith("ed"):
        base = word[:-2]

        if len(base) >= 3:
            return base

    if (
        len(word) > 4
        and word.endswith("s")
        and not word.endswith("ss")
    ):
        return word[:-1]

    return word


def get_word_set(text):

    words = re.findall(
        r"[A-Za-z][A-Za-z0-9+#./-]*",
        normalize(text)
    )

    return {
        normalize_word(word)
        for word in words
        if len(word) >= 2
    }


# =========================================================
# PDF ANALYSIS
# =========================================================

def extract_pdf_information(file_path):

    document = fitz.open(file_path)

    pages_text = []

    blocks_count = 0
    total_spans = 0

    font_sizes = []
    font_names = []

    image_count = 0

    suspicious_short_lines = 0
    total_lines = 0

    page_dimensions = []

    for page in document:

        page_text = page.get_text("text")

        pages_text.append(page_text)

        page_dimensions.append(
            (
                round(page.rect.width, 2),
                round(page.rect.height, 2)
            )
        )

        blocks = page.get_text("blocks")

        blocks_count += len(blocks)

        image_count += len(
            page.get_images(full=True)
        )

        dictionary = page.get_text("dict")

        for block in dictionary.get("blocks", []):

            if "lines" not in block:
                continue

            for line in block["lines"]:

                total_lines += 1

                line_text = ""

                for span in line.get("spans", []):

                    total_spans += 1

                    span_text = span.get(
                        "text",
                        ""
                    )

                    line_text += span_text

                    size = span.get("size")
                    font = span.get("font")

                    if size:
                        font_sizes.append(
                            round(size, 1)
                        )

                    if font:
                        font_names.append(
                            str(font)
                        )

                if (
                    line_text.strip()
                    and len(line_text.strip()) <= 2
                ):
                    suspicious_short_lines += 1

    page_count = len(document)

    document.close()

    text = clean_text(
        "\n".join(pages_text)
    )

    unique_font_sizes = sorted(
        set(font_sizes)
    )

    unique_fonts = sorted(
        set(font_names)
    )

    return {
        "text": text,
        "page_count": page_count,
        "blocks_count": blocks_count,
        "total_spans": total_spans,
        "unique_font_sizes": unique_font_sizes,
        "unique_fonts": unique_fonts,
        "font_size_count": len(unique_font_sizes),
        "font_count": len(unique_fonts),
        "image_count": image_count,
        "total_lines": total_lines,
        "suspicious_short_lines": suspicious_short_lines,
        "page_dimensions": page_dimensions
    }


# =========================================================
# CONTACT INFORMATION
# =========================================================

def detect_email(text):

    pattern = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}\b"
    )

    match = re.search(pattern, text)

    return match.group(0) if match else None


def detect_phone(text):

    patterns = [
        r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",

        r"(?<!\d)(?:\+91[\s-]?)?"
        r"[6-9]\d{4}[\s-]?\d{5}(?!\d)"
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if match:
            return match.group(0)

    return None


def detect_linkedin(text):

    match = re.search(
        r"(?:https?://)?"
        r"(?:www\.)?"
        r"linkedin\.com/[^\s]+",
        text,
        re.IGNORECASE
    )

    return match.group(0) if match else None


def detect_github(text):

    match = re.search(
        r"(?:https?://)?"
        r"(?:www\.)?"
        r"github\.com/[^\s]+",
        text,
        re.IGNORECASE
    )

    return match.group(0) if match else None


# =========================================================
# SECTION DETECTION
# =========================================================

def detect_sections(text):

    lines = []

    for raw_line in text.splitlines():

        cleaned = re.sub(
            r"[^a-zA-Z/& ]",
            "",
            raw_line
        )

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned
        ).strip().lower()

        if cleaned:
            lines.append(cleaned)

    results = {}

    for section, names in SECTION_PATTERNS.items():

        found = False

        for line in lines:

            for name in names:

                if (
                    line == name
                    or (
                        len(line) <= 45
                        and name in line
                    )
                ):
                    found = True
                    break

            if found:
                break

        results[section] = found

    return results


# =========================================================
# TOKENIZATION
# =========================================================

def tokenize(text):

    words = re.findall(
        r"[A-Za-z][A-Za-z0-9+#./-]*",
        text.lower()
    )

    cleaned = []

    ignored = (
        STOP_WORDS
        | JD_FILLER_WORDS
    )

    for word in words:

        word = word.strip(".,/-")

        if (
            len(word) >= 2
            and word not in ignored
        ):
            cleaned.append(word)

    return cleaned


# =========================================================
# JD SENTENCES
# =========================================================

def split_sentences(text):

    text = text.replace("\n", ". ")

    parts = re.split(
        r"[.!?;]+",
        text
    )

    return [
        normalize(part)
        for part in parts
        if normalize(part)
    ]


# =========================================================
# EXTRACT MEANINGFUL JD TERMS
# =========================================================

def extract_dynamic_keywords(job_description):

    raw_words = re.findall(
        r"[A-Za-z][A-Za-z0-9+#./-]*",
        job_description.lower()
    )

    ignored = (
        STOP_WORDS
        | JD_FILLER_WORDS
        | GENERIC_JD_VERBS
    )

    terms = []
    seen_normalized = set()

    for word in raw_words:

        word = word.strip(".,/-")

        if len(word) < 2:
            continue

        if word in ignored:
            continue

        canonical = normalize_word(word)

        if canonical in ignored:
            continue

        if len(canonical) < 2:
            continue

        if canonical not in seen_normalized:

            seen_normalized.add(canonical)

            terms.append(word)

    return terms


# =========================================================
# EXTRACT MEANINGFUL JD PHRASES
# =========================================================

def extract_phrases(job_description):

    sentences = split_sentences(
        job_description
    )

    phrase_counter = Counter()

    ignored = (
        STOP_WORDS
        | JD_FILLER_WORDS
    )

    for sentence in sentences:

        tokens = re.findall(
            r"[a-z][a-z0-9+#./-]*",
            sentence
        )

        # Bigrams and trigrams
        for size in (3, 2):

            for index in range(
                len(tokens) - size + 1
            ):

                group = tokens[
                    index:index + size
                ]

                useful = [
                    word
                    for word in group
                    if word not in ignored
                ]

                # At least 2 meaningful words
                # are necessary.
                if len(useful) < 2:
                    continue

                # Reject phrases that begin/end
                # almost entirely with filler wording.
                if (
                    group[0] in JD_FILLER_WORDS
                    and group[-1] in JD_FILLER_WORDS
                ):
                    continue

                phrase = " ".join(group)

                phrase_counter[phrase] += 1

    phrases = list(
        phrase_counter.keys()
    )

    # Prefer phrases containing more meaningful words
    # and repeated concepts.
    phrases.sort(
        key=lambda phrase: (
            -len(phrase.split()),
            -phrase_counter[phrase],
            job_description.lower().find(phrase)
        )
    )

    # Remove redundant phrases.
    selected = []

    for phrase in phrases:

        if any(
            phrase == existing
            for existing in selected
        ):
            continue

        selected.append(phrase)

    return selected


# =========================================================
# SINGLE TERM MATCHING
# =========================================================

def term_present(
    term,
    resume_text
):

    resume_words = get_word_set(
        resume_text
    )

    canonical = normalize_word(
        term
    )

    return canonical in resume_words


# =========================================================
# PHRASE MATCHING
# =========================================================

def phrase_present(
    phrase,
    resume_text
):

    resume_normalized = normalize(
        resume_text
    )

    phrase_normalized = normalize(
        phrase
    )

    # Direct phrase match first.
    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(phrase_normalized)
        + r"(?![a-z0-9])"
    )

    if re.search(
        pattern,
        resume_normalized
    ):
        return True

    # Conservative normalized token comparison.
    phrase_words = [
        normalize_word(word)
        for word in phrase_normalized.split()
        if word not in STOP_WORDS
        and word not in JD_FILLER_WORDS
    ]

    if len(phrase_words) < 2:
        return False

    resume_words = get_word_set(
        resume_text
    )

    return all(
        word in resume_words
        for word in phrase_words
    )


# =========================================================
# REMOVE TERMS ALREADY REPRESENTED BY PHRASES
# =========================================================

def reduce_keyword_overlap(
    keywords,
    phrases
):

    phrase_words = set()

    for phrase in phrases:

        words = phrase.split()

        for word in words:

            if (
                word not in STOP_WORDS
                and word not in JD_FILLER_WORDS
            ):
                phrase_words.add(
                    normalize_word(word)
                )

    reduced = []

    for keyword in keywords:

        canonical = normalize_word(
            keyword
        )

        # Keep independent terms too,
        # but avoid excessive phrase duplication.
        if canonical not in phrase_words:
            reduced.append(keyword)

    # If every keyword was represented
    # by phrases, keep original terms.
    if not reduced:
        return keywords

    return reduced


# =========================================================
# JOB MATCH
# =========================================================

def calculate_job_match(
    resume_text,
    job_description
):

    keywords = extract_dynamic_keywords(
        job_description
    )

    phrases = extract_phrases(
        job_description
    )

    # Prevent the same concept being counted
    # repeatedly as phrase + every component word.
    scoring_keywords = reduce_keyword_overlap(
        keywords,
        phrases
    )

    matched_keywords = []
    missing_keywords = []

    for keyword in scoring_keywords:

        if term_present(
            keyword,
            resume_text
        ):

            matched_keywords.append(
                keyword
            )

        else:

            missing_keywords.append(
                keyword
            )

    matched_phrases = []
    missing_phrases = []

    for phrase in phrases:

        if phrase_present(
            phrase,
            resume_text
        ):

            matched_phrases.append(
                phrase
            )

        else:

            missing_phrases.append(
                phrase
            )

    keyword_total = len(
        scoring_keywords
    )

    phrase_total = len(
        phrases
    )

    if keyword_total:

        keyword_score = (
            len(matched_keywords)
            / keyword_total
        ) * 100

    else:
        keyword_score = 0

    if phrase_total:

        phrase_score = (
            len(matched_phrases)
            / phrase_total
        ) * 100

    else:
        phrase_score = 0

    # Phrases are stronger evidence than
    # isolated words.
    if keyword_total and phrase_total:

        score = round(
            keyword_score * 0.55
            +
            phrase_score * 0.45
        )

    elif phrase_total:

        score = round(
            phrase_score
        )

    else:

        score = round(
            keyword_score
        )

    evidence = [
        (
            f"{len(matched_keywords)} of "
            f"{keyword_total} meaningful JD terms "
            f"were detected in the resume."
        ),

        (
            f"{len(matched_phrases)} of "
            f"{phrase_total} meaningful JD phrases "
            f"were detected in the resume."
        )
    ]

    return {
        "score":
            min(max(score, 0), 100),

        "matched_keywords":
            matched_keywords,

        "missing_keywords":
            missing_keywords,

        "matched_phrases":
            matched_phrases,

        "missing_phrases":
            missing_phrases,

        "evidence":
            evidence
    }


# =========================================================
# ROLE RELEVANCE
# =========================================================

def calculate_role_relevance(
    resume_text,
    job_role,
    job_description,
    job_match
):

    role_terms = []

    for word in tokenize(job_role):

        canonical = normalize_word(word)

        if canonical not in [
            normalize_word(x)
            for x in role_terms
        ]:
            role_terms.append(word)

    matched_role_terms = []

    for term in role_terms:

        if term_present(
            term,
            resume_text
        ):

            matched_role_terms.append(
                term
            )

    if role_terms:

        direct_role_score = (
            len(matched_role_terms)
            / len(role_terms)
        ) * 100

    else:

        direct_role_score = 0

    # JD alignment is the main evidence.
    # Exact title words are only supporting evidence.
    score = round(
        job_match["score"] * 0.90
        +
        direct_role_score * 0.10
    )

    evidence = [
        (
            f"{len(matched_role_terms)} of "
            f"{len(role_terms)} target-role terms "
            f"were directly detected in the resume."
        ),

        (
            f"Job-description alignment contributes "
            f"the primary role evidence "
            f"({job_match['score']}/100)."
        )
    ]

    return {
        "score":
            min(max(score, 0), 100),

        "matched_role_terms":
            matched_role_terms,

        "role_terms":
            role_terms,

        "evidence":
            evidence
    }


# =========================================================
# ATS SCORE
# =========================================================

def calculate_ats_score(
    pdf_info,
    email,
    phone,
    sections
):

    text = pdf_info["text"]

    word_count = len(
        text.split()
    )

    score = 0

    breakdown = []
    evidence = []

    # -------------------------
    # TEXT EXTRACTABILITY /20
    # -------------------------

    if word_count >= 150:

        extractability = 20

        evidence.append(
            "PDF contains substantial "
            "machine-readable text."
        )

    elif word_count >= 75:

        extractability = 15

        evidence.append(
            "PDF contains machine-readable text, "
            "but extracted content is limited."
        )

    elif word_count >= 30:

        extractability = 8

        evidence.append(
            "Only a small amount of "
            "machine-readable text was extracted."
        )

    else:

        extractability = 0

        evidence.append(
            "Very little machine-readable "
            "text was extracted."
        )

    score += extractability

    breakdown.append({
        "name": "PDF Text Extractability",
        "score": extractability,
        "max": 20
    })

    # -------------------------
    # CONTACT /20
    # -------------------------

    contact_score = 0

    if email:

        contact_score += 10

        evidence.append(
            "Email address detected."
        )

    else:

        evidence.append(
            "Email address was not detected."
        )

    if phone:

        contact_score += 10

        evidence.append(
            "Phone number detected."
        )

    else:

        evidence.append(
            "Phone number was not detected."
        )

    score += contact_score

    breakdown.append({
        "name": "Contact Information",
        "score": contact_score,
        "max": 20
    })

    # -------------------------
    # SECTIONS /30
    # -------------------------

    important_sections = [
        "Summary / Objective",
        "Education",
        "Experience",
        "Projects",
        "Skills"
    ]

    detected_count = sum(
        1
        for section in important_sections
        if sections.get(section)
    )

    section_score = round(
        detected_count
        / len(important_sections)
        * 30
    )

    score += section_score

    breakdown.append({
        "name": "Standard Resume Sections",
        "score": section_score,
        "max": 30
    })

    evidence.append(
        f"{detected_count} of "
        f"{len(important_sections)} "
        f"common resume sections were detected."
    )

    # -------------------------
    # FORMATTING /30
    # -------------------------

    formatting = 0

    page_count = pdf_info[
        "page_count"
    ]

    if 1 <= page_count <= 2:

        formatting += 8

        evidence.append(
            f"Resume length is "
            f"{page_count} page(s)."
        )

    elif page_count == 3:

        formatting += 5

        evidence.append(
            "Resume contains 3 pages."
        )

    else:

        evidence.append(
            f"Resume contains "
            f"{page_count} pages."
        )

    font_count = pdf_info[
        "font_count"
    ]

    if 1 <= font_count <= 4:

        formatting += 7

        evidence.append(
            "Font usage appears "
            "reasonably consistent."
        )

    elif font_count <= 7:

        formatting += 4

        evidence.append(
            f"{font_count} font families "
            f"were detected."
        )

    else:

        evidence.append(
            f"{font_count} font families "
            f"were detected."
        )

    font_size_count = pdf_info[
        "font_size_count"
    ]

    if 2 <= font_size_count <= 7:

        formatting += 7

        evidence.append(
            "A manageable font-size "
            "hierarchy was detected."
        )

    elif font_size_count == 1:

        formatting += 4

        evidence.append(
            "Only one font size was detected."
        )

    elif font_size_count <= 10:

        formatting += 3

        evidence.append(
            "Several font sizes were detected."
        )

    else:

        evidence.append(
            "A large number of font sizes "
            "were detected."
        )

    image_count = pdf_info[
        "image_count"
    ]

    if image_count <= 2:

        formatting += 4

        evidence.append(
            f"{image_count} image(s) detected; "
            f"the PDF is not heavily "
            f"image-dependent."
        )

    else:

        evidence.append(
            f"{image_count} images were detected; "
            f"image-heavy layouts can be harder "
            f"for some ATS parsers."
        )

    total_lines = max(
        pdf_info["total_lines"],
        1
    )

    fragment_ratio = (
        pdf_info[
            "suspicious_short_lines"
        ]
        / total_lines
    )

    if fragment_ratio < 0.20:

        formatting += 4

        evidence.append(
            "Extracted text does not show "
            "excessive fragmentation."
        )

    else:

        evidence.append(
            "Extracted text contains many "
            "very short fragments."
        )

    formatting = min(
        formatting,
        30
    )

    score += formatting

    breakdown.append({
        "name": "Formatting & Structure",
        "score": formatting,
        "max": 30
    })

    return {
        "score":
            min(max(score, 0), 100),

        "breakdown":
            breakdown,

        "evidence":
            evidence
    }


# =========================================================
# CONTENT QUALITY
# =========================================================

def calculate_content_score(
    text,
    sections
):

    normalized = normalize(text)

    word_count = len(
        text.split()
    )

    score = 0

    breakdown = []
    evidence = []

    # -------------------------
    # SUBSTANCE /20
    # -------------------------

    if 250 <= word_count <= 900:
        substance = 20

    elif 150 <= word_count < 250:
        substance = 15

    elif 75 <= word_count < 150:
        substance = 8

    elif word_count > 900:
        substance = 15

    else:
        substance = 3

    score += substance

    breakdown.append({
        "name": "Content Substance",
        "score": substance,
        "max": 20
    })

    evidence.append(
        f"Resume contains "
        f"{word_count} words."
    )

    # -------------------------
    # CORE SECTIONS /30
    # -------------------------

    content_sections = [
        "Summary / Objective",
        "Education",
        "Experience",
        "Projects",
        "Skills"
    ]

    section_count = sum(
        1
        for section in content_sections
        if sections.get(section)
    )

    section_score = round(
        section_count
        / len(content_sections)
        * 30
    )

    score += section_score

    breakdown.append({
        "name": "Core Content Sections",
        "score": section_score,
        "max": 30
    })

    evidence.append(
        f"{section_count} of "
        f"{len(content_sections)} "
        f"core content sections were detected."
    )

    # -------------------------
    # ACTION LANGUAGE /20
    # -------------------------

    found_verbs = sorted({
        verb
        for verb in ACTION_VERBS
        if re.search(
            r"\b"
            + re.escape(verb)
            + r"\b",
            normalized
        )
    })

    if len(found_verbs) >= 6:
        action_score = 20

    elif len(found_verbs) >= 4:
        action_score = 15

    elif len(found_verbs) >= 2:
        action_score = 10

    elif len(found_verbs) == 1:
        action_score = 5

    else:
        action_score = 0

    score += action_score

    breakdown.append({
        "name": "Action-Oriented Language",
        "score": action_score,
        "max": 20
    })

    if found_verbs:

        evidence.append(
            "Action-oriented terms detected: "
            + ", ".join(found_verbs[:8])
            + "."
        )

    else:

        evidence.append(
            "Limited action-oriented language "
            "was detected."
        )

    # -------------------------
    # MEASURABLE EVIDENCE /15
    # -------------------------

    quantified = re.findall(
        r"\b\d+(?:\.\d+)?%"
        r"|\b\d+\+"
        r"|\b(?:₹|\$|€|£)\s?\d+"
        r"|\b\d+\s+"
        r"(?:users|clients|projects|students|"
        r"customers|members|employees|reports|"
        r"tasks|cases)\b",
        text,
        re.IGNORECASE
    )

    quant_count = len(
        quantified
    )

    if quant_count >= 4:
        quant_score = 15

    elif quant_count >= 2:
        quant_score = 10

    elif quant_count == 1:
        quant_score = 5

    else:
        quant_score = 0

    score += quant_score

    breakdown.append({
        "name": "Measurable Evidence",
        "score": quant_score,
        "max": 15
    })

    evidence.append(
        f"{quant_count} measurable or "
        f"quantified expression(s) were detected."
    )

    # -------------------------
    # SUPPORTING SECTIONS /15
    # -------------------------

    supporting_sections = [
        "Certifications",
        "Achievements",
        "Languages"
    ]

    supporting_count = sum(
        1
        for section in supporting_sections
        if sections.get(section)
    )

    supporting_score = round(
        supporting_count
        / len(supporting_sections)
        * 15
    )

    score += supporting_score

    breakdown.append({
        "name": "Supporting Sections",
        "score": supporting_score,
        "max": 15
    })

    evidence.append(
        f"{supporting_count} of "
        f"{len(supporting_sections)} "
        f"supporting sections were detected."
    )

    return {
        "score":
            min(max(score, 0), 100),

        "breakdown":
            breakdown,

        "evidence":
            evidence,

        "action_verbs":
            found_verbs,

        "quantified_count":
            quant_count
    }


# =========================================================
# RESUME ANALYSIS
# =========================================================

def calculate_resume_analysis_score(
    ats,
    content,
    sections,
    email,
    phone
):

    detected_sections = sum(
        1
        for value in sections.values()
        if value
    )

    total_sections = len(
        sections
    )

    structure_score = round(
        detected_sections
        / total_sections
        * 100
    )

    contact_score = 0

    if email:
        contact_score += 50

    if phone:
        contact_score += 50

    score = round(
        ats["score"] * 0.35
        +
        content["score"] * 0.35
        +
        structure_score * 0.20
        +
        contact_score * 0.10
    )

    breakdown = [
        {
            "name": "ATS Compatibility",
            "value": ats["score"],
            "weight": "35%"
        },

        {
            "name": "Content Quality",
            "value": content["score"],
            "weight": "35%"
        },

        {
            "name": "Resume Structure",
            "value": structure_score,
            "weight": "20%"
        },

        {
            "name": "Contact Completeness",
            "value": contact_score,
            "weight": "10%"
        }
    ]

    evidence = [
        (
            f"ATS Compatibility: "
            f"{ats['score']}/100 "
            f"(35% of Resume Analysis Score)."
        ),

        (
            f"Content Quality: "
            f"{content['score']}/100 "
            f"(35%)."
        ),

        (
            f"{detected_sections} of "
            f"{total_sections} analyzed resume "
            f"sections were detected, producing "
            f"a structure score of "
            f"{structure_score}/100 (20%)."
        ),

        (
            f"Contact completeness score: "
            f"{contact_score}/100 (10%)."
        )
    ]

    return {
        "score":
            min(max(score, 0), 100),

        "breakdown":
            breakdown,

        "evidence":
            evidence,

        "structure_score":
            structure_score,

        "contact_score":
            contact_score
    }


# =========================================================
# SUGGESTIONS
# =========================================================

def build_suggestions(
    email,
    phone,
    linkedin,
    sections,
    ats,
    content,
    job_match
):

    suggestions = []

    if not email:

        suggestions.append(
            "An email address was not detected. "
            "Add a professional email address."
        )

    if not phone:

        suggestions.append(
            "A phone number was not detected. "
            "Add a valid contact number."
        )

    if not sections.get(
        "Summary / Objective"
    ):

        suggestions.append(
            "A Summary or Objective section was "
            "not detected. Consider adding a concise "
            "professional summary when appropriate."
        )

    if not sections.get("Skills"):

        suggestions.append(
            "A clearly labelled Skills section "
            "was not detected."
        )

    if (
        not sections.get("Experience")
        and
        not sections.get("Projects")
    ):

        suggestions.append(
            "Neither an Experience nor Projects "
            "section was detected. Where applicable, "
            "include relevant employment, internship, "
            "academic project or practical evidence."
        )

    if content[
        "quantified_count"
    ] == 0:

        suggestions.append(
            "No clear measurable achievements "
            "were detected. Where truthful, support "
            "achievements with numbers, percentages, "
            "scale or measurable outcomes."
        )

    if len(
        content["action_verbs"]
    ) < 2:

        suggestions.append(
            "Limited action-oriented language was "
            "detected. Where accurate, describe work "
            "using clear action-focused statements."
        )

    missing_phrases = job_match[
        "missing_phrases"
    ]

    missing_keywords = job_match[
        "missing_keywords"
    ]

    missing_for_suggestion = (
        missing_phrases[:5]
        +
        missing_keywords[:5]
    )

    if missing_for_suggestion:

        suggestions.append(
            "Some requirements from the supplied "
            "job description were not detected in "
            "the resume: "
            + ", ".join(missing_for_suggestion)
            + ". Add only requirements that "
            "truthfully match your actual skills "
            "or experience."
        )

    if ats["score"] < 70:

        suggestions.append(
            "ATS compatibility is below 70. "
            "Review the ATS evidence for missing "
            "standard sections, contact information "
            "or formatting indicators."
        )

    if not linkedin:

        suggestions.append(
            "A LinkedIn URL was not detected. "
            "Consider including a professional "
            "profile when relevant."
        )

    return suggestions[:8]


# =========================================================
# MAIN ANALYZER
# =========================================================

def analyze_resume(
    file_path,
    job_role,
    job_description
):

    job_role = job_role.strip()

    job_description = (
        job_description.strip()
    )

    if not job_role:

        raise ValueError(
            "Target Job Role is required."
        )

    if not job_description:

        raise ValueError(
            "Job Description is required."
        )

    # Fresh PDF analysis for every upload.
    pdf_info = extract_pdf_information(
        file_path
    )

    text = pdf_info["text"]

    if not text:

        raise ValueError(
            "No machine-readable text was "
            "found in the uploaded PDF."
        )

    if len(text.split()) < 20:

        raise ValueError(
            "The PDF contains too little "
            "readable resume text for "
            "reliable analysis."
        )

    # Fresh resume evidence.
    email = detect_email(text)

    phone = detect_phone(text)

    linkedin = detect_linkedin(text)

    github = detect_github(text)

    sections = detect_sections(text)

    # Fresh component scores.
    ats = calculate_ats_score(
        pdf_info,
        email,
        phone,
        sections
    )

    content = calculate_content_score(
        text,
        sections
    )

    job_match = calculate_job_match(
        text,
        job_description
    )

    role_relevance = (
        calculate_role_relevance(
            text,
            job_role,
            job_description,
            job_match
        )
    )

    resume_analysis = (
        calculate_resume_analysis_score(
            ats,
            content,
            sections,
            email,
            phone
        )
    )

    # =====================================================
    # OVERALL SCORE
    # =====================================================

    overall_raw = (
        resume_analysis["score"] * 0.20
        +
        ats["score"] * 0.20
        +
        job_match["score"] * 0.30
        +
        role_relevance["score"] * 0.15
        +
        content["score"] * 0.15
    )

    overall_score = round(
        overall_raw
    )

    overall_breakdown = [
        {
            "name": "Resume Analysis",
            "score": resume_analysis["score"],
            "weight": "20%"
        },

        {
            "name": "ATS Compatibility",
            "score": ats["score"],
            "weight": "20%"
        },

        {
            "name": "Job Match",
            "score": job_match["score"],
            "weight": "30%"
        },

        {
            "name": "Role Relevance",
            "score": role_relevance["score"],
            "weight": "15%"
        },

        {
            "name": "Content Quality",
            "score": content["score"],
            "weight": "15%"
        }
    ]

    suggestions = build_suggestions(
        email,
        phone,
        linkedin,
        sections,
        ats,
        content,
        job_match
    )

    return {
        "overall_score":
            overall_score,

        "resume_analysis_score":
            resume_analysis["score"],

        "ats_score":
            ats["score"],

        "job_match_score":
            job_match["score"],

        "role_relevance_score":
            role_relevance["score"],

        "content_score":
            content["score"],

        "overall_breakdown":
            overall_breakdown,

        "resume_analysis_breakdown":
            resume_analysis["breakdown"],

        "ats_breakdown":
            ats["breakdown"],

        "content_breakdown":
            content["breakdown"],

        "resume_analysis_evidence":
            resume_analysis["evidence"],

        "ats_evidence":
            ats["evidence"],

        "job_match_evidence":
            job_match["evidence"],

        "role_evidence":
            role_relevance["evidence"],

        "content_evidence":
            content["evidence"],

        "matched_keywords":
            job_match["matched_keywords"],

        "missing_keywords":
            job_match["missing_keywords"],

        "matched_phrases":
            job_match["matched_phrases"],

        "missing_phrases":
            job_match["missing_phrases"],

        "role_terms":
            role_relevance["role_terms"],

        "matched_role_terms":
            role_relevance[
                "matched_role_terms"
            ],

        "sections":
            sections,

        "contact": {
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github
        },

        "suggestions":
            suggestions,

        "page_count":
            pdf_info["page_count"],

        "word_count":
            len(text.split()),

        "font_count":
            pdf_info["font_count"],

        "font_size_count":
            pdf_info["font_size_count"],

        "image_count":
            pdf_info["image_count"],

        "resume_preview":
            text[:8000],

        "job_description":
            job_description
    }