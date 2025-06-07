import re
from typing import List, Dict
import tiktoken


def count_tokens(text: str, tokenizer_name: str = "cl100k_base") -> int:
    """
    Return the number of tokens in 'text' according to the specified tokenizer.
    """
    enc = tiktoken.get_encoding(tokenizer_name)
    return len(enc.encode(text))

def forced_sentence_split(long_text: str, max_tokens: int) -> List[str]:
    """
    Split long_text in half at the nearest sentence boundary if it exceeds max_tokens,
    recursing until all parts are within the token limit.
    """
    if count_tokens(long_text) <= max_tokens:
        return [long_text]
    midpoint = len(long_text) // 2
    pattern = re.compile(r"\.[ ]+[A-Z]")
    left = long_text[:midpoint]
    right = long_text[midpoint:]

    m_left = list(pattern.finditer(left))
    if m_left:
        split_pos = m_left[-1].end() - 1
    else:
        m_right = list(pattern.finditer(right))
        if m_right:
            split_pos = midpoint + m_right[0].start() + 1
        else:
            split_pos = midpoint

    part1 = long_text[:split_pos].strip()
    part2 = long_text[split_pos:].strip()
    return forced_sentence_split(part1, max_tokens) + forced_sentence_split(part2, max_tokens)

def split_by_markdown_delimiter(text: str) -> List[str]:
    """
    Split text by any of the following in order:
      1. fenced code blocks (```), horizontal rules (---, ***)
      2. blank lines (paragraph breaks)
      3. list items (- , *, or numbered)
    If no delimiter found, return [text].
    """
    lines = text.splitlines(keepends=True)
    splits = []
    curr = ""
    for line in lines:
        if re.match(r"^(?:```|---|\*\*\*)", line):
            if curr.strip():
                splits.append(curr)
                curr = ""
            splits.append(line)
        else:
            curr += line
    if curr.strip():
        splits.append(curr)
    if len(splits) > 1:
        return splits

    paragraphs = re.split(r"\n\s*\n", text)
    if len(paragraphs) > 1:
        return [p + "\n\n" for p in paragraphs]

    list_splits = re.split(r"(?m)^(?:- |\* |\d+\.\s+)", text)
    if len(list_splits) > 1:
        return list(filter(lambda s: s.strip(), list_splits))

    return [text]

def recursive_split_by_hierarchy_and_delimiters(
    text: str,
    headings: List[Dict],
    start_line: int,
    end_line: int,
    max_tokens: int
) -> List[Dict]:
    """
    Recursively split a text block into chunks, respecting:
      1. Heading-based splits (levels 2-6)
      2. Markdown delimiters (code fences, paragraphs, lists)
      3. Forced sentence splits if still too large

    Returns a list of dicts:
      { "text": <chunk_text>,
        "own_heading": <heading_text or None>,
        "start_line": <int>,
        "end_line": <int> }
    """

    # Base case: if text is empty, nothing to do
    if not text.strip():
        return []

    # 1) Find headings within [start_line, end_line)
    local_headings = [h for h in headings if start_line <= h["line_no"] < end_line]

    # 2) If no headings, attempt delimiter or forced split
    if not local_headings:
        # If under token limit, return as‐is
        if count_tokens(text) <= max_tokens:
            return [{ "text": text, "own_heading": None, "start_line": start_line, "end_line": end_line }]

        # Try splitting on Markdown delimiters
        parts = split_by_markdown_delimiter(text)
        # If no real split occurred, forced sentence split
        if len(parts) == 1 and parts[0] == text:
            pieces = forced_sentence_split(text, max_tokens)
            chunks = []
            offset = 0
            for piece in pieces:
                sub_end = start_line + piece.count("\n") + offset
                # If forced split didn’t shrink, bail out
                if piece == text:
                    return [{ "text": text, "own_heading": None, "start_line": start_line, "end_line": end_line }]
                chunks.extend(recursive_split_by_hierarchy_and_delimiters(
                    piece, headings,
                    start_line + offset, sub_end,
                    max_tokens
                ))
                offset += piece.count("\n")
            return chunks

        # True delimiter split; recurse on each part
        chunks = []
        curr_line = start_line
        for part in parts:
            sub_end = curr_line + part.count("\n")
            if part == text:
                # Bail out if we’re not shrinking
                return [{ "text": text, "own_heading": None, "start_line": start_line, "end_line": end_line }]
            sub_chunks = recursive_split_by_hierarchy_and_delimiters(
                part, headings,
                curr_line, sub_end,
                max_tokens
            )
            chunks.extend(sub_chunks)
            curr_line = sub_end
        return chunks

    # 3) There are headings. Find the lowest level among them.
    min_level = min(h["level"] for h in local_headings)
    splits = [h for h in local_headings if h["level"] == min_level]

    # 4) Guard: if exactly one heading at start_line, skip heading-based split
    if len(splits) == 1 and splits[0]["line_no"] == start_line:
        if count_tokens(text) <= max_tokens:
            return [{ "text": text, "own_heading": splits[0]["heading_text"], "start_line": start_line, "end_line": end_line }]

        # Try Markdown delimiters
        parts = split_by_markdown_delimiter(text)
        if len(parts) == 1 and parts[0] == text:
            # Forced split
            pieces = forced_sentence_split(text, max_tokens)
            chunks = []
            offset = 0
            for piece in pieces:
                sub_end = start_line + piece.count("\n") + offset
                if piece == text:
                    return [{ "text": text, "own_heading": splits[0]["heading_text"], "start_line": start_line, "end_line": end_line }]
                chunks.extend(recursive_split_by_hierarchy_and_delimiters(
                    piece, headings,
                    start_line + offset, sub_end,
                    max_tokens
                ))
                offset += piece.count("\n")
            return chunks

        # True delimiter split; recurse
        chunks = []
        curr_line = start_line
        for part in parts:
            sub_end = curr_line + part.count("\n")
            if part == text:
                return [{ "text": text, "own_heading": splits[0]["heading_text"], "start_line": start_line, "end_line": end_line }]
            sub_chunks = recursive_split_by_hierarchy_and_delimiters(
                part, headings,
                curr_line, sub_end,
                max_tokens
            )
            chunks.extend(sub_chunks)
            curr_line = sub_end
        return chunks

    # 5) Otherwise, split on all headings at min_level
    chunks = []
    for i, h in enumerate(splits):
        sub_start = h["line_no"]
        next_boundary = splits[i+1]["line_no"] if i+1 < len(splits) else end_line
        sub_lines = text.splitlines()[sub_start - start_line : next_boundary - start_line]
        sub_text = "\n".join(sub_lines)
        if sub_text == text:
            return [{ "text": text, "own_heading": h["heading_text"], "start_line": start_line, "end_line": end_line }]
        sub_chunks = recursive_split_by_hierarchy_and_delimiters(
            sub_text, headings,
            sub_start, next_boundary,
            max_tokens
        )
        chunks.extend(sub_chunks)

    return chunks

