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
    # Pattern to find fenced code blocks or horizontal rules
    # It will match ```...``` or --- or ***
    # We want to split the text by these, keeping the delimiters as separate chunks if they are rules,
    # or keeping the entire code block as one chunk.

    # regex: (```[\s\S]*?```|^(?:---|\*\*\*)$)
    # [\s\S]*? is a non-greedy match for any character including newline
    delimiter_pattern = re.compile(r'(?m)(```[\s\S]*?```|^(?:---|\*\*\*)$)')

    parts = []
    last_end = 0
    has_delimiter_split = False

    for match in delimiter_pattern.finditer(text):
        start, end = match.span()
        # Add text before the delimiter
        if start > last_end:
            parts.append(text[last_end:start])

        # Add the delimiter itself (which is a full code block or a rule line)
        parts.append(match.group(0))
        last_end = end
        has_delimiter_split = True

    # Add any remaining text after the last delimiter
    if last_end < len(text):
        parts.append(text[last_end:])

    # Filter out empty strings that might result from adjacent delimiters or start/end of string
    # However, code blocks themselves should not be stripped if they are just whitespace internally.
    # The main goal is to split by these structures.
    # If parts contains only the original text, it means no delimiters were found by this pattern.
    if has_delimiter_split and parts:
        # If the splitting results in empty strings between delimiters, remove them,
        # unless the original text was just a delimiter.
        # E.g., if text = "```code```", parts will be ["```code```"].
        # If text = "text1\\n```code```\\ntext2", parts will be ["text1\\n", "```code```", "\\ntext2"].
        # If text = "```code1```\\n```code2```", parts will be ["```code1```", "\\n", "```code2```"] if \\n between.
        # Or ["```code1```", "```code2```"] if no space.
        # The filter(str.strip) is too aggressive as it removes whitespace-only code blocks or parts.
        # We just need to ensure we don't return [original_text] if a split happened.

        # A better check: if the number of non-empty parts is more than one,
        # or if the single part is different from the original text (meaning it's a delimiter itself).
        non_empty_parts = [p for p in parts if p] # Keep parts that are not empty strings
        if len(non_empty_parts) > 1 or (len(non_empty_parts) == 1 and non_empty_parts[0] != text):
             return non_empty_parts
        elif not non_empty_parts and text: # Original text was non-empty but all parts became empty (e.g. text="\\n")
             pass # Fall through to paragraph splitter
        elif not text: # Original text was empty
             return []


    # If no code blocks or rules split the text, try paragraph splitting
    # Ensure paragraphs end with double newlines if they are not the last.
    paragraphs = re.split(r'(\n\s*\n)', text) # Simpler regex, keep one double newline group
    if len(paragraphs) > 1:
        result_paragraphs = []
        # Iterate through content and delimiter pairs (or content, delimiter, content...)
        for i in range(len(paragraphs)):
            part = paragraphs[i]
            is_delimiter = bool(re.fullmatch(r'\n\s*\n', part)) # Check if THIS part is a delimiter

            if i % 2 == 0: # Content part
                if part.strip(): # If content is not just whitespace
                    # If next part is a delimiter, add it to current content
                    if i + 1 < len(paragraphs) and re.fullmatch(r'\n\s*\n', paragraphs[i+1]):
                        result_paragraphs.append(part + paragraphs[i+1])
                    else:
                        result_paragraphs.append(part)
            # Delimiter parts are handled by adding them to the preceding content part
            # Or if a content part was empty, this logic effectively skips standalone delimiters.

        # Filter out any purely whitespace entries that might have resulted
        result_paragraphs = [p for p in result_paragraphs if p.strip()]

        if len(result_paragraphs) > 1 or (len(result_paragraphs)==1 and result_paragraphs[0] != text):
            return result_paragraphs
        elif not result_paragraphs and text.strip(): # Original text was non-empty but all parts became empty
             pass # Fall through
        elif not text.strip() and not result_paragraphs : #Original text was empty or whitespace
             return [] # Return empty list if original text was empty/whitespace and no paragraphs found


    # If still no meaningful split, try list item splitting


    # If still no meaningful split, try list item splitting
    # This regex needs to be careful not to break list items internally.
    # (?m)^(?:- |\* |\d+\.\s+)
    # We want to split *between* list items.
    # A simpler approach might be to find lines starting with list markers.
    lines = text.splitlines(keepends=True)
    if len(lines) > 1: # Only attempt if there's more than one line
        list_item_pattern = re.compile(r"^(?:- |\* |\d+\.\s+)")
        current_chunk_lines = []
        split_chunks = []
        is_list_active = False

        for line in lines:
            is_list_line = bool(list_item_pattern.match(line))
            if is_list_line:
                if not is_list_active and current_chunk_lines: # End of a non-list block
                    split_chunks.append("".join(current_chunk_lines))
                    current_chunk_lines = []
                is_list_active = True
                current_chunk_lines.append(line)
            else: # Not a list line
                if is_list_active: # End of a list block
                    if current_chunk_lines:
                        split_chunks.append("".join(current_chunk_lines))
                    current_chunk_lines = []
                    is_list_active = False
                current_chunk_lines.append(line)

        if current_chunk_lines: # Append any remaining part
            split_chunks.append("".join(current_chunk_lines))

        # Filter out potential empty strings from splitting if necessary
        final_list_splits = [s for s in split_chunks if s.strip()]
        if len(final_list_splits) > 1:
            return final_list_splits
        elif len(final_list_splits) == 1 and final_list_splits[0] != text and text.strip(): # Made a change
             return final_list_splits


    return [text] # Fallback: return the original text as a single chunk

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
            # Check if this single, unsplittable part is a code block
            stripped_part = parts[0].strip()
            if stripped_part.startswith("```") and stripped_part.endswith("```"):
                # It's a single code block. Keep it as one chunk, even if over max_tokens.
                # Further splitting by sentence logic would damage it.
                return [{"text": parts[0], "own_heading": None, "start_line": start_line, "end_line": end_line}]
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
            # Check if this single, unsplittable part is a code block
            stripped_part = parts[0].strip()
            if stripped_part.startswith("```") and stripped_part.endswith("```"):
                # It's a single code block. Keep it as one chunk, even if over max_tokens.
                # Further splitting by sentence logic would damage it.
                return [{"text": parts[0], "own_heading": splits[0]["heading_text"], "start_line": start_line, "end_line": end_line}]
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

