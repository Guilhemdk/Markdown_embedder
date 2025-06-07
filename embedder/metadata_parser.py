import os
import re
from typing import List, Dict, Optional
from nltk.corpus import stopwords



def parse_topic_from_filename(filename: str) -> str:
    """
    Extract the topic from a filename like "06_markdown_generation_memory.md".
    Returns "markdown_generation".
    """
    base = os.path.basename(filename)[:-3]
    parts = base.split("_")
    return "_".join(parts[1:-1])

def parse_version_context(full_text: str) -> Optional[str]:
    """
    Find a line "Library Version Context: X.Y.Z" and return the version string.
    """
    for line in full_text.splitlines():
        m = re.search(r"Library Version Context:\s*(\S+)", line)
        if m:
            return m.group(1)
    return None

def parse_outline_date(full_text: str) -> Optional[str]:
    """
    Find a date "YYYY-MM-DD" on the "Library Version Context" line or top 10 lines.
    """
    for line in full_text.splitlines():
        if "Library Version Context" in line:
            m = re.search(r"(\d{4}-\d{2}-\d{2})", line)
            if m:
                return m.group(1)
    for line in full_text.splitlines()[:10]:
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\s*$", line)
        if m:
            return m.group(1)
    return None

def extract_headings(full_text: str) -> List[Dict]:
    """
    Extract all level 2-6 Markdown headings, capturing:

    - level (2..6),
    - optional numeric prefix (e.g. "2.3"),
    - the rest of the heading text.

    Returns a list of dicts:
      {
        "line_no": <int>,
        "level": <2..6>,
        "section_number": <"2.3" or None>,
        "heading_text": "<the text after any number>"
      }
    """
    headings = []
    for i, line in enumerate(full_text.splitlines()):
        # Match “## 2.3. Something” OR “## Something”
        m = re.match(r"^(#{2,6})\s*(?:([0-9]+(?:\.[0-9]+)*)\.\s*)?(.+)$", line)
        if m:
            level = len(m.group(1))
            sec_num = m.group(2)  # None if no numeric prefix
            text = m.group(3).strip()
            headings.append({
                "line_no": i,
                "level": level,
                "section_number": sec_num,
                "heading_text": text
            })
    return headings

def get_headings_only(chunk_text: str) -> List[str]:
    """
    Return a list of heading_texts (without '#') for level 2-6 headings in chunk_text.
    """
    titles = []
    for line in chunk_text.splitlines():
        m = re.match(r"^#{2,6}\s*(?:[0-9]+(?:\.[0-9]+)*)?\.\s*(.+)$", line)
        if m:
            titles.append(m.group(1).strip())
    return titles

def extract_keywords(chunk_text: str, custom_stop: Optional[List[str]] = None) -> List[str]:
    """
    Find backtick-wrapped tokens and CamelCase identifiers, filter by stoplist.
    Return up to 10 keywords.
    """
    code_terms = re.findall(r"`([^`]+)`", chunk_text)
    camel = re.findall(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)*\b", chunk_text)
    candidates = set(code_terms + camel)

    eng_stop = set(stopwords.words("english"))
    domain_stop = {"Config", "Memory", "Data", "Strategy", "Class", "Function", "Implementation"}
    if custom_stop:
        combined_stop = domain_stop.union(eng_stop).union(set(custom_stop))
    else:
        combined_stop = domain_stop.union(eng_stop)

    keywords = sorted([w for w in candidates if w not in combined_stop and len(w) > 2])
    return keywords[:7]

def extract_description(chunk_text: str) -> str:
    """
    Extract description from "* Description:" or "** ... Purpose:" lines.
    If neither is found, return an empty string.
    """
    purpose_text = None

    for line in chunk_text.splitlines():
        # Check for "** N.M Purpose:"
        m1 = re.match(r"^\*\*\s*[0-9]+(?:\.[0-9]+)*\s+Purpose:\s*(.+)$", line)
        if m1 and purpose_text is None:
            purpose_text = m1.group(1).strip()

        # Check for "* Description:" (highest precedence)
        m2 = re.match(r"^\*\s*Description:\s*(.+)$", line)
        if m2:
            return m2.group(1).strip()

    if purpose_text:
        return purpose_text

    return ""

