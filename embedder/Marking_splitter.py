import re
from typing import List, Dict
import tiktoken
import logging

# Global log prefix for this module
LOG_PREFIX = "[MS_TRACE]"

# Helper to log snippets of text
def log_snippet(log_text, max_len=150):
    if not isinstance(log_text, str):
        try:
            log_text = str(log_text)
        except:
            return "[Error converting to string]"
    if len(log_text) > max_len:
        return f"{log_text[:max_len // 2]}...{log_text[-(max_len // 2):]}"
    return log_text


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
    print(f"{LOG_PREFIX}  split_by_markdown_delimiter: Input snippet: '{log_snippet(text.strip())}' ({count_tokens(text)} tokens)")

    # Check if the entire input string, after stripping, starts with ``` and ends with ```.
    # This is the most direct way to identify if the whole input is one code block.
    stripped_text = text.strip()
    if stripped_text.startswith("```") and stripped_text.endswith("```"):
        # To ensure it's a legitimate block and not just "``` ```" or "``` some text",
        # we can check if there are at least two lines or if the content inside is substantial.
        # However, for this fix, the primary goal is: if it looks like a complete block, preserve it.
        # The original 'text' (with its original surrounding whitespace) is returned.
        print(f"{LOG_PREFIX}  split_by_markdown_delimiter: Detected as a whole code block. Returning as 1 part.")
        return [text]

    # --- Fallback to previous logic if the above condition is not met ---
    # (This is the logic that was reported as working by the subtask worker previously
    # for splitting text that contains code blocks among other elements)

    delimiter_pattern = re.compile(r'(?m)(```[\s\S]*?```|^(?:---|\*\*\*)$)')
    parts = []
    last_end = 0
    has_delimiter_split = False

    for match in delimiter_pattern.finditer(text):
        start, end = match.span()
        if start > last_end:
            parts.append(text[last_end:start])
        parts.append(match.group(0))
        last_end = end
        has_delimiter_split = True

    if last_end < len(text):
        parts.append(text[last_end:])

    if has_delimiter_split and parts:
        non_empty_parts = [p for p in parts if p]
        if len(non_empty_parts) > 1 or (len(non_empty_parts) == 1 and non_empty_parts[0] != text):
            print(f"{LOG_PREFIX}  split_by_markdown_delimiter: Found {len(non_empty_parts)} parts after delimiter pattern. Has_delimiter_split: {has_delimiter_split}. Snippets: {[log_snippet(p.strip()) for p in non_empty_parts[:3]]}...")
            return non_empty_parts
        elif not non_empty_parts and text and text.strip():
            # This case implies original text was only delimiters or whitespace around them.
            print(f"{LOG_PREFIX}  split_by_markdown_delimiter: Delimiter split resulted in no non-empty parts from non-empty text. Original may have been only delimiters.")
            pass # Fall through to paragraph splitting
        elif not text:
            print(f"{LOG_PREFIX}  split_by_markdown_delimiter: Input text is empty. Returning empty list.")
            return []
        # If only one part and it's the same as original, or other edge cases, fall through
        print(f"{LOG_PREFIX}  split_by_markdown_delimiter: Delimiter pattern found but resulted in 1 part or no effective split. Parts: {len(non_empty_parts)}. Has_delimiter_split: {has_delimiter_split}. Proceeding to paragraph split.")


    # Paragraph splitting (simplified for clarity, focusing on double newlines with optional whitespace)
    # This part might need the more robust version from worker if issues arise here for non-code text
    para_parts = re.split(r'(\n\s*\n)', text)
    processed_para_parts = []
    if len(para_parts) > 1: # Potential split
        current_piece = ""
        for i, piece in enumerate(para_parts):
            current_piece += piece
            if i % 2 == 1: # It's a delimiter (\n\s*\n)
                if current_piece.strip(): # Keep the delimiter as part of the preceding paragraph
                    processed_para_parts.append(current_piece)
                current_piece = ""
        if current_piece.strip(): # Add the last piece if it's not empty
             processed_para_parts.append(current_piece)

        print(f"{LOG_PREFIX}  split_by_markdown_delimiter: Found {len(para_parts)} potential para_parts (raw split). Processed into {len(processed_para_parts)} non-empty paragraph parts.")
        if not processed_para_parts and text.strip(): # If all parts were whitespace or empty after processing
            print(f"{LOG_PREFIX}  split_by_markdown_delimiter: Paragraph splitting resulted in no processable parts from non-empty text.")
            pass # Fall through
        elif len(processed_para_parts) > 1 or (processed_para_parts and processed_para_parts[0] != text):
            # Only return if it actually split into multiple parts or changed the text
            return_parts_snippets = [log_snippet(p.strip()) for p in processed_para_parts[:3]]
            print(f"{LOG_PREFIX}  split_by_markdown_delimiter: Returning {len(processed_para_parts)} parts from paragraph split. Snippets: {return_parts_snippets}...")
            return processed_para_parts
        else:
            print(f"{LOG_PREFIX}  split_by_markdown_delimiter: Paragraph splitting did not result in a meaningful split ({len(processed_para_parts)} part(s)).")


    # List item splitting (simplified, placeholder - robust list splitting is complex)
    # This might need the more robust version from worker if list splitting is critical
    lines = text.splitlines(keepends=True)
    if len(lines) > 1:
        list_item_pattern = re.compile(r"^(?:- |\* |\d+\.\s+)")
        is_list_chunk = all(list_item_pattern.match(line) for line in lines if line.strip())
        if is_list_chunk and len(lines) > 1 : # A very basic attempt if all lines are list items
             # This is not a good general list splitter, just a placeholder
             # The version from the subtask worker was more elaborate and should be preferred
             # if this simplified part causes issues. For now, this is a fallback.
             pass # Fall through, let original text be returned

    return_parts_snippets = [log_snippet(text.strip())] # Only one part if reaches here
    print(f"{LOG_PREFIX}  split_by_markdown_delimiter: No effective split by delimiter or paragraph. Returning 1 part. Snippet: {return_parts_snippets}...")
    return [text]

# Helper to count lines accurately
def count_text_lines(text_content: str) -> int:
    if not text_content: return 0
    # splitlines() handles various newline characters and doesn't count a final newline if present before EOF
    # A non-empty string with no newlines is 1 line. An empty string is 0 lines.
    # "foo" -> 1 line. "foo\n" -> 1 line. "foo\nbar" -> 2 lines.
    num_lines = len(text_content.splitlines())
    if text_content == "\n": # Special case for a string that is just one newline
        return 1
    if not num_lines and text_content: # Non-empty string but no newlines (e.g. "foo")
        return 1
    return num_lines


def _split_python_code_by_functions(code_text: str, max_tokens: int, doc_start_line_of_code_block: int) -> List[Dict]:
    print(f"{LOG_PREFIX}    _split_python_code_by_functions: Input code block ({count_text_lines(code_text)} lines, {count_tokens(code_text)} tokens) starting original doc line {doc_start_line_of_code_block}. Snippet: '{log_snippet(code_text.strip())}'")

    # Regex to find 'def' or 'async def' at the beginning of a line, capturing function name.
    # (?P<name>...) creates a named capture group.
    # Need to be careful with indentation; this regex assumes functions are not deeply nested within other structures
    # in a way that would make this simple line-based regex fail.
    func_pattern = re.compile(r"^[ 	]*(?:async def|def)\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)")

    # Extract content within the fences before matching functions
    block_lines = code_text.splitlines(keepends=True)
    if len(block_lines) < 2 or not block_lines[0].strip().startswith("```") or not block_lines[-1].strip().startswith("```"):
        # Not a valid fenced block or too short, return original
        # # print(f"[FUNC_SPLIT] Invalid or short fenced block. Lines: {len(block_lines)}. Start: '{block_lines[0] if block_lines else ''}'. End: '{block_lines[-1] if len(block_lines)>1 else ''}'")
        num_lines = count_text_lines(code_text)
        end_line = doc_start_line_of_code_block + num_lines -1 if num_lines > 0 else doc_start_line_of_code_block
        return [{"text": code_text, "own_heading": "Code Block (Malformed/Short)", "start_line": doc_start_line_of_code_block, "end_line": end_line}]

    code_content_text = "".join(block_lines[1:-1])
    # Line number of the first line of actual code content (after ```)
    doc_start_line_of_content = doc_start_line_of_code_block + 1

    matches = list(func_pattern.finditer(code_content_text))

    if not matches:
        print(f"{LOG_PREFIX}    _split_python_code_by_functions: No function definitions found. Returning original block.")
        num_lines = count_text_lines(code_text) # Original block lines
        end_line = doc_start_line_of_code_block + num_lines - 1 if num_lines > 0 else doc_start_line_of_code_block
        return [{"text": code_text, "own_heading": "Code Block (Full, No Functions)", "start_line": doc_start_line_of_code_block, "end_line": end_line}]

    chunks = []

    # Helper to create a chunk dict, adding back fences and calculating correct doc line numbers
    def _create_chunk_with_fences(slice_text_content, heading_prefix, slice_start_char_in_content):
        final_chunk_text = block_lines[0] + slice_text_content + block_lines[-1]

        # Absolute start line of this slice's content in the document
        # This is doc_start_line_of_content + lines before this slice *within code_content_text*
        abs_slice_content_start_line = doc_start_line_of_content + code_content_text[:slice_start_char_in_content].count('\n')

        num_content_lines = count_text_lines(slice_text_content)
        abs_slice_content_end_line = abs_slice_content_start_line + (num_content_lines - 1 if num_content_lines > 0 else 0)

        return {
            "text": final_chunk_text,
            "own_heading": heading_prefix,
            "start_line": abs_slice_content_start_line - 1, # Line of the top fence ```
            "end_line": abs_slice_content_end_line + 1      # Line of the bottom fence ```
        }

    # 1. Handle text before the first function definition (preamble)
    first_func_match_start_char = matches[0].start()
    if first_func_match_start_char > 0: # Check if there's any text before the first match
        preamble_content_slice = code_content_text[0:first_func_match_start_char]
        if preamble_content_slice.strip():
            chunks.append(_create_chunk_with_fences(preamble_content_slice, "Code Segment (Preamble)", 0))

    # 2. Handle each function and the text between them (which becomes part of the function's chunk)
    for i, match in enumerate(matches):
        func_name = match.group("name")

        start_of_current_func_content_char = match.start()
        # End of the current function's content is start of next function's content, or end of code_content_text
        end_of_current_func_content_char = matches[i+1].start() if i + 1 < len(matches) else len(code_content_text)

        function_content_slice = code_content_text[start_of_current_func_content_char:end_of_current_func_content_char]

        if function_content_slice.strip():
            chunks.append(_create_chunk_with_fences(function_content_slice, f"Function: {func_name}", start_of_current_func_content_char))

    if not chunks:
        print(f"{LOG_PREFIX}    _split_python_code_by_functions: No chunks created despite finding functions (e.g. all preamble/functions were whitespace). Returning original.")
        num_lines = count_text_lines(code_text)
        end_line = doc_start_line_of_code_block + num_lines - 1 if num_lines > 0 else doc_start_line_of_code_block
        return [{"text": code_text, "own_heading": "Code Block (Full, Error in Splitting by Func)", "start_line": doc_start_line_of_code_block, "end_line": end_line}]

    if len(chunks) == 1 and chunks[0]["text"].strip() == code_text.strip():
        print(f"{LOG_PREFIX}    _split_python_code_by_functions: Splitting by function resulted in the original block effectively. No change.")
        # Ensure original line numbers and heading are preserved if not actually split
        num_lines = count_text_lines(code_text)
        end_line = doc_start_line_of_code_block + num_lines - 1 if num_lines > 0 else doc_start_line_of_code_block
        chunks[0]["own_heading"] = "Code Block (Full, Not Split by Function)"
        chunks[0]["start_line"] = doc_start_line_of_code_block
        chunks[0]["end_line"] = end_line
        return chunks # Return the single chunk list

    chunk_func_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
    print(f"{LOG_PREFIX}    _split_python_code_by_functions: Returning {len(chunks)} chunks by function. Details (first 3): {chunk_func_details_log}")
    return chunks

def recursive_split_by_hierarchy_and_delimiters(
    text: str,
    headings: List[Dict],
    start_line: int,
    end_line: int,
    max_tokens: int,
    _depth: int = 0  # Internal depth counter for logging
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

    indent = "  " * _depth
    print(f"{LOG_PREFIX}{indent}Depth {_depth}: Processing lines {start_line}-{end_line}. Input text snippet: '{log_snippet(text.strip())}' ({count_tokens(text)} tokens)")

    # 1) Find headings within [start_line, end_line)
    local_headings = [h for h in headings if start_line <= h["line_no"] < end_line]
    if local_headings:
        heading_details = [(h['heading_text'], h['level'], h['line_no']) for h in local_headings]
        print(f"{LOG_PREFIX}{indent}  Found {len(local_headings)} local headings: {heading_details[:3]}...")
    else:
        print(f"{LOG_PREFIX}{indent}  No local headings found.")

    # 2) If no headings, attempt delimiter or forced split
    if not local_headings:
        print(f"{LOG_PREFIX}{indent}  Branch: No local headings.")
        if count_tokens(text) <= max_tokens:
            print(f"{LOG_PREFIX}{indent}  Text under token limit ({count_tokens(text)} <= {max_tokens}). Returning as single chunk.")
            chunks = [{ "text": text, "own_heading": None, "start_line": start_line, "end_line": end_line }]
            chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
            print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks. Details (first 3): {chunk_details_log}")
            return chunks

        print(f"{LOG_PREFIX}{indent}  Text over token limit. Attempting split_by_markdown_delimiter.")
        parts = split_by_markdown_delimiter(text)
        print(f"{LOG_PREFIX}{indent}  Parts from delimiter split: {len(parts)}. Snippets: {[log_snippet(p.strip()) for p in parts[:3]]}...")

        if len(parts) == 1 and parts[0] == text:
            print(f"{LOG_PREFIX}{indent}  Delimiter split resulted in no change.")
            stripped_part = parts[0].strip()
            if stripped_part.startswith("```") and stripped_part.endswith("```"):
                code_block_text = parts[0]
                if count_tokens(code_block_text) > 2 * max_tokens:
                    print(f"{LOG_PREFIX}{indent}  Code block > 2*max_tokens ({count_tokens(code_block_text)} > {2 * max_tokens}). Attempting function split for block at lines {start_line}-{end_line}.")
                    function_chunks = _split_python_code_by_functions(code_block_text, max_tokens, start_line)
                    if len(function_chunks) > 1 or (len(function_chunks) == 1 and function_chunks[0]["text"] != code_block_text) :
                        chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in function_chunks[:3]]
                        print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(function_chunks)} chunks from function split. Details: {chunk_details_log}")
                        return function_chunks
                    else:
                        print(f"{LOG_PREFIX}{indent}  Code block not split by function (or not large enough for it). Returning as is. Lines {start_line}-{end_line}.")
                        chunks = [{"text": code_block_text, "own_heading": None, "start_line": start_line, "end_line": end_line}]
                        chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
                        print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks. Details (first 3): {chunk_details_log}")
                        return chunks
                else:
                    print(f"{LOG_PREFIX}{indent}  Code block not > 2*max_tokens or already fine. Returning as is. Lines {start_line}-{end_line}.")
                    chunks = [{"text": code_block_text, "own_heading": None, "start_line": start_line, "end_line": end_line}]
                    chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
                    print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks. Details (first 3): {chunk_details_log}")
                    return chunks

            print(f"{LOG_PREFIX}{indent}  Not a code block or code block preserved. Attempting forced_sentence_split.")
            pieces = forced_sentence_split(text, max_tokens)
            print(f"{LOG_PREFIX}{indent}  Pieces from forced_sentence_split: {len(pieces)}. Snippets: {[log_snippet(p.strip()) for p in pieces[:3]]}...")

            chunks = []
            offset = 0
            doc_lines_in_text = text.count("\n")
            for i, piece in enumerate(pieces):
                # Estimate line numbers more carefully
                piece_lines = piece.count("\n")
                sub_start_abs = start_line + offset
                sub_end_abs = start_line + offset + piece_lines
                if i == len(pieces) -1 : # last piece
                    sub_end_abs = start_line + doc_lines_in_text # Ensure it goes to the end of original text's line span

                if piece == text and len(pieces) == 1: # Avoid infinite loop if forced_split returns original
                     print(f"{LOG_PREFIX}{indent}  Forced split piece is same as input. Bailing.")
                     chunks = [{ "text": text, "own_heading": None, "start_line": start_line, "end_line": end_line }]
                     break

                print(f"{LOG_PREFIX}{indent}  Recursing on forced piece {i} (approx lines {sub_start_abs}-{sub_end_abs}). Snippet: '{log_snippet(piece.strip())}' ({count_tokens(piece)} tokens)")
                chunks.extend(recursive_split_by_hierarchy_and_delimiters(
                    piece, headings,
                    sub_start_abs, sub_end_abs,
                    max_tokens, _depth + 1
                ))
                offset += piece_lines
                if i < len(pieces) -1 : # Add one for the newline that separated this piece from next
                    offset +=1

            chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
            print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks from forced split recursion. Details (first 3): {chunk_details_log}")
            return chunks

        chunks = []
        curr_abs_line = start_line
        text_lines_processed_in_parts = 0
        for i, part in enumerate(parts):
            part_lines = part.count("\n")
            sub_start_abs = curr_abs_line
            sub_end_abs = curr_abs_line + part_lines

            if part == text and len(parts) == 1: # Should not happen if split was effective
                print(f"{LOG_PREFIX}{indent}  Delimiter part is same as input. Bailing.")
                chunks = [{ "text": text, "own_heading": None, "start_line": start_line, "end_line": end_line }]
                break

            print(f"{LOG_PREFIX}{indent}  Recursing on delimiter part {i} (approx lines {sub_start_abs}-{sub_end_abs}). Snippet: '{log_snippet(part.strip())}' ({count_tokens(part)} tokens)")
            sub_chunks = recursive_split_by_hierarchy_and_delimiters(
                part, headings,
                sub_start_abs, sub_end_abs,
                max_tokens, _depth + 1
            )
            chunks.extend(sub_chunks)
            curr_abs_line = sub_end_abs
            if i < len(parts) -1: # Account for the implicit newline delimiter if not the last part
                 # This assumes split_by_markdown_delimiter parts are separated by something that implies a line break.
                 # Or, more accurately, the line numbers of parts should be calculated based on their content from original text.
                 # The previous line counting `curr_line = sub_end` was problematic.
                 # For now, `sub_end_abs` becomes the next `sub_start_abs`.
                 pass


        chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
        print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks from delimiter part recursion. Details (first 3): {chunk_details_log}")
        return chunks

    # 3) There are headings. Find the lowest level among them.
    min_level = min(h["level"] for h in local_headings)
    splits = [h for h in local_headings if h["level"] == min_level]
    # print(f"{LOG_PREFIX}{indent}  Min heading level: {min_level}. Found {len(splits)} headings at this level: {[(s['heading_text'], s['line_no']) for s in splits[:3]]}...")


    # 4) Guard: if exactly one heading at start_line, skip heading-based split
    if len(splits) == 1 and splits[0]["line_no"] == start_line:
        current_heading_text = splits[0]["heading_text"]
        print(f"{LOG_PREFIX}{indent}  Branch: Single heading guard for '{splits[0]['heading_text']}' at line {start_line}.")

        if count_tokens(text) <= max_tokens:
            print(f"{LOG_PREFIX}{indent}  (Single heading) Text under token limit ({count_tokens(text)} <= {max_tokens}). Returning as single chunk with heading.")
            chunks = [{ "text": text, "own_heading": current_heading_text, "start_line": start_line, "end_line": end_line }]
            chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
            print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks. Details (first 3): {chunk_details_log}")
            return chunks

        print(f"{LOG_PREFIX}{indent}  (Single heading) Text over token limit. Attempting split_by_markdown_delimiter.")
        parts = split_by_markdown_delimiter(text)
        print(f"{LOG_PREFIX}{indent}  (Single heading) Parts from delimiter split: {len(parts)}. Snippets: {[log_snippet(p.strip()) for p in parts[:3]]}...")

        if len(parts) == 1 and parts[0] == text:
            print(f"{LOG_PREFIX}{indent}  (Single heading) Delimiter split resulted in no change.")
            stripped_part = parts[0].strip()
            if stripped_part.startswith("```") and stripped_part.endswith("```"):
                code_block_text = parts[0]
                if count_tokens(code_block_text) > 2 * max_tokens:
                    print(f"{LOG_PREFIX}{indent}  (Single heading) Code block > 2*max_tokens. Attempting function split for block at lines {start_line}-{end_line}.")
                    function_chunks = _split_python_code_by_functions(code_block_text, max_tokens, start_line)
                    if len(function_chunks) > 1 or (len(function_chunks) == 1 and function_chunks[0]["text"] != code_block_text):
                        for fc in function_chunks:
                             if fc.get("own_heading") is None or "Code Block" in fc.get("own_heading", "") : fc["own_heading"] = current_heading_text
                        chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in function_chunks[:3]]
                        print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(function_chunks)} chunks from function split. Details: {chunk_details_log}")
                        return function_chunks
                    else: # Not split by function or not effective
                        print(f"{LOG_PREFIX}{indent}  (Single heading) Code block not split by function. Returning as is. Lines {start_line}-{end_line}.")
                        chunks = [{"text": code_block_text, "own_heading": current_heading_text, "start_line": start_line, "end_line": end_line}]
                        chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
                        print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks. Details (first 3): {chunk_details_log}")
                        return chunks
                else: # Code block not > 2 * max_tokens
                    print(f"{LOG_PREFIX}{indent}  (Single heading) Code block not > 2*max_tokens. Returning as is. Lines {start_line}-{end_line}.")
                    chunks = [{"text": code_block_text, "own_heading": current_heading_text, "start_line": start_line, "end_line": end_line}]
                    chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
                    print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks. Details (first 3): {chunk_details_log}")
                    return chunks

            print(f"{LOG_PREFIX}{indent}  (Single heading) Not a code block or preserved. Attempting forced_sentence_split.")
            pieces = forced_sentence_split(text, max_tokens)
            print(f"{LOG_PREFIX}{indent}  (Single heading) Pieces from forced_sentence_split: {len(pieces)}. Snippets: {[log_snippet(p.strip()) for p in pieces[:3]]}...")
            chunks = []
            offset = 0
            doc_lines_in_text = text.count("\n")
            for i, piece in enumerate(pieces):
                piece_lines = piece.count("\n")
                sub_start_abs = start_line + offset
                sub_end_abs = start_line + offset + piece_lines
                if i == len(pieces) -1 : sub_end_abs = start_line + doc_lines_in_text

                if piece == text and len(pieces) == 1:
                    print(f"{LOG_PREFIX}{indent}  (Single heading) Forced split piece is same as input. Bailing.")
                    chunks = [{ "text": text, "own_heading": current_heading_text, "start_line": start_line, "end_line": end_line }]
                    break

                print(f"{LOG_PREFIX}{indent}  (Single heading) Recursing on forced piece {i} (approx lines {sub_start_abs}-{sub_end_abs}). Snippet: '{log_snippet(piece.strip())}' ({count_tokens(piece)} tokens)")
                temp_chunks = recursive_split_by_hierarchy_and_delimiters(
                    piece, headings, sub_start_abs, sub_end_abs, max_tokens, _depth + 1 )
                for tc in temp_chunks:
                    if tc.get("own_heading") is None: tc["own_heading"] = current_heading_text
                chunks.extend(temp_chunks)
                offset += piece_lines
                if i < len(pieces) -1 : offset +=1

            chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
            print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks from forced split (single heading). Details: {chunk_details_log}")
            return chunks

        # True delimiter split (single heading context)
        chunks = []
        curr_abs_line = start_line # This needs to be absolute from document start
        for i, part in enumerate(parts):
            part_lines = part.count("\n")
            sub_start_abs = curr_abs_line
            sub_end_abs = curr_abs_line + part_lines

            if part == text and len(parts) == 1: # Should not happen
                print(f"{LOG_PREFIX}{indent}  (Single heading) Delimiter part is same as input. Bailing.")
                chunks = [{ "text": text, "own_heading": current_heading_text, "start_line": start_line, "end_line": end_line }]
                break

            print(f"{LOG_PREFIX}{indent}  (Single heading) Recursing on delimiter part {i} (approx lines {sub_start_abs}-{sub_end_abs}). Snippet: '{log_snippet(part.strip())}' ({count_tokens(part)} tokens)")
            temp_chunks = recursive_split_by_hierarchy_and_delimiters(
                part, headings, sub_start_abs, sub_end_abs, max_tokens, _depth + 1 )
            for tc in temp_chunks:
                if tc.get("own_heading") is None: tc["own_heading"] = current_heading_text
            chunks.extend(temp_chunks)
            curr_abs_line = sub_end_abs # Next part starts where this one ended (line-wise)
            # Need to ensure line accounting is correct from original `text` string for `curr_abs_line` if parts don't include all newlines.

        chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
        print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks from delimiter recursion (single heading). Details: {chunk_details_log}")
        return chunks

    # 5) Otherwise, split on all headings at min_level
    print(f"{LOG_PREFIX}{indent}  Branch: Splitting by {len(splits)} headings of level {min_level}. Headings: {[(s['heading_text'], s['line_no']) for s in splits[:3]]}...")
    chunks = []

    # Iterate through the split points (headings at min_level)
    # The text for each sub-problem starts at a heading `h` and ends just before the next heading `splits[i+1]`
    # or at `end_line` if `h` is the last heading in `splits`.

    for i, h in enumerate(splits):
        sub_start_abs = h["line_no"]
        sub_end_abs = splits[i+1]["line_no"] if i+1 < len(splits) else end_line

        # Extract the text segment corresponding to this heading `h`
        # This requires careful slicing of the original `text` based on absolute line numbers.
        lines_in_original_text = text.splitlines(keepends=True)

        # Calculate start and end indices for slicing `lines_in_original_text`
        # `start_line` is the absolute line number of the beginning of `text`
        slice_start_idx = sub_start_abs - start_line
        slice_end_idx = sub_end_abs - start_line

        # Ensure indices are valid for `lines_in_original_text`
        slice_start_idx = max(0, min(slice_start_idx, len(lines_in_original_text)))
        slice_end_idx = max(0, min(slice_end_idx, len(lines_in_original_text)))

        if slice_start_idx >= slice_end_idx: # Empty segment
            # print(f"{LOG_PREFIX}{indent}  Skipping empty segment for heading '{h['heading_text']}' (lines {sub_start_abs}-{sub_end_abs})")
            continue

        sub_text = "".join(lines_in_original_text[slice_start_idx:slice_end_idx])

        if not sub_text.strip():
            # print(f"{LOG_PREFIX}{indent}  Skipping effectively empty sub_text for heading '{h['heading_text']}' (lines {sub_start_abs}-{sub_end_abs})")
            continue

        # This is the critical check: if sub_text is the same as the input `text` AND we only have one split point `h`,
        # it means this function was called with `text` that *is* the content under `h`.
        # This should have been caught by the "single heading guard" if `h` was at `start_line`.
        # If `h` is not at `start_line` but is the only split, it implies content before `h` was empty or non-existent.
        if sub_text == text and len(splits) == 1:
            # This situation should ideally be handled by the single heading guard.
            # If it occurs, it means the current `text` block is precisely the content of this `h`.
            # We assign `h`'s text as its own_heading and recurse to break it down further if needed.
            # However, to prevent infinite loops, if we are here, it implies that the single heading guard
            # condition (h["line_no"] == start_line) was NOT met.
            # This means `text` might be *exactly* `sub_text` but `h` is not at `text`'s start.
            # This is okay, proceed to recurse. The `own_heading` will be `h['heading_text']`.
            # print(f"{LOG_PREFIX}{indent}  Sub-text for '{h['heading_text']}' is same as input text, but not caught by single guard. Proceeding.")
            # The recursive call below will handle this. It will become a "single heading at start_line" case for the sub-problem.
            pass


        print(f"{LOG_PREFIX}{indent}  Recursing on heading split for '{h['heading_text']}' (lines {sub_start_abs}-{sub_end_abs}). Snippet: '{log_snippet(sub_text.strip())}' ({count_tokens(sub_text)} tokens)")
        sub_chunks = recursive_split_by_hierarchy_and_delimiters(
            sub_text, headings,
            sub_start_abs, sub_end_abs,
            max_tokens, _depth + 1
        )

        # Assign owning heading if sub-chunks don't have one (they should, from their own processing)
        # This is a fallback: normally, the recursive call should set the correct heading.
        # If a sub_chunk's own_heading is None, it means it's direct content under h.
        for sc in sub_chunks:
            if sc.get("own_heading") is None:
                sc["own_heading"] = h["heading_text"]
        chunks.extend(sub_chunks)

    chunk_details_log = [(log_snippet(c['text'].strip()), c.get('own_heading', 'N/A'), c['start_line'], c['end_line']) for c in chunks[:3]]
    print(f"{LOG_PREFIX}{indent}Depth {_depth}: Returning {len(chunks)} chunks from multi-heading split. Details (first 3): {chunk_details_log}")
    return chunks
