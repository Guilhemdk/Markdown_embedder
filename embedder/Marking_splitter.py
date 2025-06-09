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
    # Print the exact input for crucial debugging
    # print(f"[SBMD_TRACE] Input received: '{text}'") # Can be very verbose

    # Check if the entire input string, after stripping, starts with ``` and ends with ```.
    # This is the most direct way to identify if the whole input is one code block.
    stripped_text = text.strip()
    if stripped_text.startswith("```") and stripped_text.endswith("```"):
        # To ensure it's a legitimate block and not just "``` ```" or "``` some text",
        # we can check if there are at least two lines or if the content inside is substantial.
        # However, for this fix, the primary goal is: if it looks like a complete block, preserve it.
        # The original 'text' (with its original surrounding whitespace) is returned.
        # print(f"[SBMD_TRACE] Detected as a whole code block. Input: '{text[:100]}...', Stripped: '{stripped_text[:100]}...'")
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
            return non_empty_parts
        elif not non_empty_parts and text and text.strip():
            pass
        elif not text:
            return []

    # Paragraph splitting (simplified for clarity, focusing on double newlines with optional whitespace)
    # This part might need the more robust version from worker if issues arise here for non-code text
    para_parts = re.split(r'(\n\s*\n)', text) # Using the regex that was confirmed to work before simplification attempt.
    processed_para_parts = []
    if len(para_parts) > 1:
        current_piece = ""
        for i, piece in enumerate(para_parts):
            current_piece += piece
            if i % 2 == 1: # It's a delimiter
                if current_piece.strip():
                    processed_para_parts.append(current_piece)
                current_piece = ""
        if current_piece.strip(): # Last piece
             processed_para_parts.append(current_piece)

        if not processed_para_parts and text.strip(): # If all parts were whitespace
            pass
        elif len(processed_para_parts) > 1 or (processed_para_parts and processed_para_parts[0] != text):
            return processed_para_parts


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

    return [text]

# Helper function to split Python code by functions
def _split_python_code_by_functions(code_text: str, max_tokens: int, original_start_line: int) -> List[Dict]:
    print(f"[FUNC_SPLIT] Attempting to split code block (length {len(code_text)}, tokens {count_tokens(code_text)}) at original_start_line {original_start_line}")
    # Placeholder: In a real scenario, this would use regex to find 'def' and 'async def'.
    # For now, to test the flow, it just returns the original block.
    # A more complete regex would be: pattern = re.compile(r"^([ \t]*)(async def|def)\s+([a-zA-Z_][a-zA-Z0-9_]*)")
    # This is a simplified "no-op" version for the subtask to ensure the main logic path is tested.
    print(f"[FUNC_SPLIT] Function splitting not fully implemented, returning original block.")
    # Calculate end_line based on original_start_line and newlines in code_text
    num_newlines = code_text.count('\n')
    calculated_end_line = original_start_line + num_newlines
    return [{"text": code_text, "own_heading": "Code Block (Function Splitting Placeholder)", "start_line": original_start_line, "end_line": calculated_end_line}]

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

    def log_snippet(log_text, max_len=150):
        if len(log_text) > max_len:
            return f"{log_text[:max_len // 2]}...{log_text[-(max_len // 2):]}"
        return log_text

    indent = "  " * _depth
    print(f"{indent}[R_SPLIT_DEBUG] Depth {_depth}: Processing lines {start_line}-{end_line}. Input text: {log_snippet(text.strip())}")

    # 1) Find headings within [start_line, end_line)
    local_headings = [h for h in headings if start_line <= h["line_no"] < end_line]
    if local_headings:
        heading_details = [(h['heading_text'], h['level']) for h in local_headings]
        print(f"{indent}[R_SPLIT_DEBUG] Found {len(local_headings)} local headings: {heading_details}")
    else:
        print(f"{indent}[R_SPLIT_DEBUG] No local headings found.")

    # 2) If no headings, attempt delimiter or forced split
    if not local_headings:
        print(f"{indent}[R_SPLIT_DEBUG] Branch: No local headings.")
        # If under token limit, return as‐is
        if count_tokens(text) <= max_tokens:
            print(f"{indent}[R_SPLIT_DEBUG] Text under token limit ({count_tokens(text)} <= {max_tokens}). Returning as single chunk.")
            return [{ "text": text, "own_heading": None, "start_line": start_line, "end_line": end_line }]

        # Try splitting on Markdown delimiters
        print(f"{indent}[R_SPLIT_DEBUG] Text over token limit. Calling split_by_markdown_delimiter for: {log_snippet(text.strip())}")
        parts = split_by_markdown_delimiter(text)
        print(f"{indent}[R_SPLIT_DEBUG] Parts from delimiter split: {len(parts)}. Snippets: {[log_snippet(p.strip()) for p in parts]}")

        # If no real split occurred, forced sentence split
        if len(parts) == 1 and parts[0] == text:
            print(f"{indent}[R_SPLIT_DEBUG] Delimiter split resulted in no change (1 part equals original text).")
            # Check if this single, unsplittable part is a code block
            stripped_part = parts[0].strip()
            if stripped_part.startswith("```") and stripped_part.endswith("```"):
                code_block_text = parts[0]
                # EXTREME DEBUG: Print the exact code block text being preserved.
                print(f"{indent}[R_SPLIT_DEBUG] FINAL PRESERVATION CHECK for code block at lines {start_line}-{end_line}: '{log_snippet(code_block_text)}'")

                if count_tokens(code_block_text) > 2 * max_tokens:
                    print(f"{indent}[R_SPLIT_DEBUG] Code block at lines {start_line}-{end_line} is > 2*max_tokens ({count_tokens(code_block_text)} > {2 * max_tokens}). Attempting function split.")
                    # Try to split by function definitions
                    function_chunks = _split_python_code_by_functions(code_block_text, max_tokens, start_line)
                    # If _split_python_code_by_functions returns more than one chunk,
                    # it means splitting was successful.
                    if len(function_chunks) > 1 or (len(function_chunks) == 1 and function_chunks[0]["text"] != code_block_text) : # check if it actually split
                        # We need to recursively process these function chunks in case they have further structure
                        # or to ensure they are properly formatted as output chunks.
                        # For now, let's assume _split_python_code_by_functions
                        # returns list of dicts that are already in the final chunk format.
                        print(f"{indent}[R_SPLIT_DEBUG] Code block at lines {start_line}-{end_line} split into {len(function_chunks)} function(s).")
                        # To avoid infinite recursion if _split_python_code_by_functions doesn't reduce size or structure:
                        # We should probably pass these to recursive_split_by_hierarchy_and_delimiters
                        # For now, directly returning them as per simplified plan.
                        return function_chunks
                    else:
                        # Splitting by function didn't work or wasn't effective, return the whole block.
                        print(f"{indent}[R_SPLIT_DEBUG] Code block at lines {start_line}-{end_line} is > 2*max_tokens but not effectively split by functions.")
                        return [{"text": code_block_text, "own_heading": None, "start_line": start_line, "end_line": end_line}]
                else:
                    # Code block is large but not > 2*max_tokens, or it's within limits after all.
                    print(f"{indent}[R_SPLIT_DEBUG] Code block at lines {start_line}-{end_line} is not > 2*max_tokens OR already fine. Returning as is.")
                    return [{"text": code_block_text, "own_heading": None, "start_line": start_line, "end_line": end_line}]

            print(f"{indent}[R_SPLIT_DEBUG] Calling forced_sentence_split for: {log_snippet(text.strip())}")
            pieces = forced_sentence_split(text, max_tokens)
            print(f"{indent}[R_SPLIT_DEBUG] Pieces from forced_sentence_split: {len(pieces)}. Snippets: {[log_snippet(p.strip()) for p in pieces]}")

            chunks = []
            offset = 0
            for i, piece in enumerate(pieces):
                sub_end = start_line + piece.count("\n") + offset # piece.count("\n") might not be perfect for line counts if piece is not raw lines
                # If forced split didn’t shrink, bail out
                if piece == text:
                    print(f"{indent}[R_SPLIT_DEBUG] Forced split piece {i} is same as input. Bailing out and returning original text as chunk.")
                    return [{ "text": text, "own_heading": None, "start_line": start_line, "end_line": end_line }]

                print(f"{indent}[R_SPLIT_DEBUG] Recursing on forced piece {i} (lines approx {start_line + offset}-{sub_end}): {log_snippet(piece.strip())}")
                chunks.extend(recursive_split_by_hierarchy_and_delimiters(
                    piece, headings,
                    start_line + offset, sub_end,
                    max_tokens, _depth + 1
                ))
                offset += piece.count("\n") # This is a simplification for line counting
            print(f"{indent}[R_SPLIT_DEBUG] Returning {len(chunks)} chunks from forced split recursion.")
            return chunks

        # True delimiter split; recurse on each part
        print(f"{indent}[R_SPLIT_DEBUG] Delimiter split resulted in {len(parts)} parts. Recursing on each.")
        chunks = []
        curr_line = start_line
        for i, part in enumerate(parts):
            sub_end = curr_line + part.count("\n")
            if part == text: # Should ideally not happen if len(parts) > 1
                print(f"{indent}[R_SPLIT_DEBUG] Delimiter part {i} is same as input. Bailing out and returning original text as chunk.")
                return [{ "text": text, "own_heading": None, "start_line": start_line, "end_line": end_line }]

            print(f"{indent}[R_SPLIT_DEBUG] Recursing on delimiter part {i} (lines approx {curr_line}-{sub_end}): {log_snippet(part.strip())}")
            sub_chunks = recursive_split_by_hierarchy_and_delimiters(
                part, headings,
                curr_line, sub_end,
                max_tokens, _depth + 1
            )
            chunks.extend(sub_chunks)
            curr_line = sub_end
        print(f"{indent}[R_SPLIT_DEBUG] Returning {len(chunks)} chunks from delimiter part recursion.")
        return chunks

    # 3) There are headings. Find the lowest level among them.
    print(f"{indent}[R_SPLIT_DEBUG] Branch: Headings found.")
    min_level = min(h["level"] for h in local_headings)
    splits = [h for h in local_headings if h["level"] == min_level]
    split_details = [(s['heading_text'], s['line_no']) for s in splits]
    print(f"{indent}[R_SPLIT_DEBUG] Min heading level: {min_level}. Found {len(splits)} headings at this level: {split_details}")

    # 4) Guard: if exactly one heading at start_line, skip heading-based split
    if len(splits) == 1 and splits[0]["line_no"] == start_line:
        current_heading_text = splits[0]["heading_text"]
        print(f"{indent}[R_SPLIT_DEBUG] Single heading '{current_heading_text}' at start_line {start_line}. Processing as a single block with this heading.")
        if count_tokens(text) <= max_tokens:
            print(f"{indent}[R_SPLIT_DEBUG] Text under token limit ({count_tokens(text)} <= {max_tokens}). Returning as single chunk with heading.")
            return [{ "text": text, "own_heading": current_heading_text, "start_line": start_line, "end_line": end_line }]

        # Try Markdown delimiters
        print(f"{indent}[R_SPLIT_DEBUG] Text over token limit. Calling split_by_markdown_delimiter for: {log_snippet(text.strip())}")
        parts = split_by_markdown_delimiter(text)
        print(f"{indent}[R_SPLIT_DEBUG] Parts from delimiter split: {len(parts)}. Snippets: {[log_snippet(p.strip()) for p in parts]}")

        if len(parts) == 1 and parts[0] == text:
            print(f"{indent}[R_SPLIT_DEBUG] Delimiter split resulted in no change.")
            # Check if this single, unsplittable part is a code block
            stripped_part = parts[0].strip()
            if stripped_part.startswith("```") and stripped_part.endswith("```"):
                code_block_text = parts[0]
                # EXTREME DEBUG: Print the exact code block text being preserved.
                print(f"{indent}[R_SPLIT_DEBUG] FINAL PRESERVATION CHECK for code block (under heading '{current_heading_text}') at lines {start_line}-{end_line}: '{log_snippet(code_block_text)}'")

                if count_tokens(code_block_text) > 2 * max_tokens:
                    print(f"{indent}[R_SPLIT_DEBUG] Code block (under heading) at lines {start_line}-{end_line} is > 2*max_tokens ({count_tokens(code_block_text)} > {2 * max_tokens}). Attempting function split.")
                    function_chunks = _split_python_code_by_functions(code_block_text, max_tokens, start_line)
                    if len(function_chunks) > 1 or (len(function_chunks) == 1 and function_chunks[0]["text"] != code_block_text):
                        print(f"{indent}[R_SPLIT_DEBUG] Code block (under heading) at lines {start_line}-{end_line} split into {len(function_chunks)} function(s).")
                        # Associate heading with these new chunks if they don't have one
                        for fc in function_chunks:
                            if fc.get("own_heading") is None or fc.get("own_heading") == "Code Block (Function Splitting Placeholder)":
                                fc["own_heading"] = current_heading_text
                        return function_chunks
                    else:
                        print(f"{indent}[R_SPLIT_DEBUG] Code block (under heading) at lines {start_line}-{end_line} > 2*max_tokens but not effectively split by functions.")
                        return [{"text": code_block_text, "own_heading": current_heading_text, "start_line": start_line, "end_line": end_line}]
                else:
                    print(f"{indent}[R_SPLIT_DEBUG] Code block (under heading) at lines {start_line}-{end_line} is not > 2*max_tokens OR already fine. Returning as is.")
                    return [{"text": code_block_text, "own_heading": current_heading_text, "start_line": start_line, "end_line": end_line}]

            print(f"{indent}[R_SPLIT_DEBUG] Calling forced_sentence_split for: {log_snippet(text.strip())}")
            pieces = forced_sentence_split(text, max_tokens)
            print(f"{indent}[R_SPLIT_DEBUG] Pieces from forced_sentence_split: {len(pieces)}. Snippets: {[log_snippet(p.strip()) for p in pieces]}")
            chunks = []
            offset = 0
            for i, piece in enumerate(pieces):
                sub_end = start_line + piece.count("\n") + offset
                if piece == text:
                    print(f"{indent}[R_SPLIT_DEBUG] Forced split piece {i} is same as input. Bailing out.")
                    return [{ "text": text, "own_heading": current_heading_text, "start_line": start_line, "end_line": end_line }]

                print(f"{indent}[R_SPLIT_DEBUG] Recursing on forced piece {i} (lines approx {start_line + offset}-{sub_end}): {log_snippet(piece.strip())}")
                # Note: Passing current_heading_text down here might be incorrect if the piece doesn't actually belong to it.
                # However, the structure implies this whole block is under this one heading.
                # For more precise heading association, recursive calls might need to pass None for heading if piece is not the start.
                # For now, keeping it simple and associating the original heading.
                temp_chunks = recursive_split_by_hierarchy_and_delimiters(
                    piece, headings, # Should these headings be filtered or is it ok?
                    start_line + offset, sub_end,
                    max_tokens, _depth + 1
                )
                # If sub-chunks don't have their own heading, associate the current one.
                for tc in temp_chunks:
                    if tc.get("own_heading") is None:
                        tc["own_heading"] = current_heading_text
                chunks.extend(temp_chunks)
                offset += piece.count("\n")
            print(f"{indent}[R_SPLIT_DEBUG] Returning {len(chunks)} chunks from forced split recursion (single heading guard).")
            return chunks

        # True delimiter split; recurse
        print(f"{indent}[R_SPLIT_DEBUG] Delimiter split resulted in {len(parts)} parts. Recursing on each (single heading guard).")
        chunks = []
        curr_line = start_line
        for i, part in enumerate(parts):
            sub_end = curr_line + part.count("\n")
            if part == text:
                print(f"{indent}[R_SPLIT_DEBUG] Delimiter part {i} is same as input. Bailing out.")
                return [{ "text": text, "own_heading": current_heading_text, "start_line": start_line, "end_line": end_line }]

            print(f"{indent}[R_SPLIT_DEBUG] Recursing on delimiter part {i} (lines approx {curr_line}-{sub_end}): {log_snippet(part.strip())}")
            # Similar heading association logic as above
            temp_chunks = recursive_split_by_hierarchy_and_delimiters(
                part, headings,
                curr_line, sub_end,
                max_tokens, _depth + 1
            )
            for tc in temp_chunks:
                if tc.get("own_heading") is None: # Only if it didn't find its own deeper heading
                    # Check if the part starts with the original heading text. Unlikely for delimiter parts.
                    # More likely, these parts are content between headings or delimiters.
                    # The current 'current_heading_text' is the one for the whole block.
                    tc["own_heading"] = current_heading_text # Associate with the main heading of this block
            chunks.extend(temp_chunks)

            curr_line = sub_end
        print(f"{indent}[R_SPLIT_DEBUG] Returning {len(chunks)} chunks from delimiter part recursion (single heading guard).")
        return chunks

    # 5) Otherwise, split on all headings at min_level
    print(f"{indent}[R_SPLIT_DEBUG] Branch: Splitting by {len(splits)} headings of level {min_level}.")
    chunks = []
    # Iterate up to the last heading to define segments.
    # The text before the first split heading (if any) needs to be handled.
    # This part of logic might be complex; the original code implies text starts with a heading or is processed before.
    # Assuming the text passed to this function starts at or before the first `h` in `splits`.

    # Let's refine how text is passed to recursive calls when splitting by headings.
    # The text from `start_line` to `splits[0]['line_no']` is content before the first split-level heading.
    # It should be processed if it's not empty and not already covered.

    current_pos_in_text = 0 # Relative to input `text`
    effective_start_line = start_line

    for i, h in enumerate(splits):
        # Segment before current heading `h`
        # `h['line_no']` is absolute. `effective_start_line` is absolute.
        # The text for the segment *before* this heading `h`
        heading_start_line_in_full_doc = h["line_no"]

        # Find where this heading `h` starts within the current `text`
        # This requires careful line counting or string searching.
        # The original `sub_lines = text.splitlines()[sub_start - start_line : next_boundary - start_line]`
        # implies that `text` is the full block for this level.

        # We are splitting the current `text` based on `splits`.
        # The first chunk is from the beginning of `text` to the start of `splits[0]`.
        # Subsequent chunks are from `splits[i]` to `splits[i+1]`.
        # The last chunk is from `splits[-1]` to the end of `text`.

        # This part of the original code seems to iterate through split points (headings)
        # and create sub_text for recursion.
        # `sub_start` is absolute line no of current heading `h`.
        # `next_boundary` is absolute line no of next heading in `splits` or `end_line`.

        # Text for the chunk associated with heading `h`
        sub_start_abs = h["line_no"]

        # Determine end of this chunk
        # If this is the last heading in `splits`, chunk goes to `end_line`
        # Otherwise, it goes to `splits[i+1]['line_no']`
        sub_end_abs = splits[i+1]["line_no"] if i+1 < len(splits) else end_line

        # Extract the actual text for this segment.
        # This requires `text` to be correctly mapped to `start_line` and `end_line`.
        # And `sub_start_abs` and `sub_end_abs` are absolute.
        # We need lines relative to the current `text` object.

        # Convert absolute line numbers to indices in current `text.splitlines()`
        lines_of_text = text.splitlines(keepends=True)

        # Offset from the start of the document to the start of the current `text` block
        doc_offset_to_text_start = start_line

        idx_h_start_in_text = sub_start_abs - doc_offset_to_text_start
        idx_h_end_in_text = sub_end_abs - doc_offset_to_text_start

        # Ensure indices are within bounds of lines_of_text
        idx_h_start_in_text = max(0, idx_h_start_in_text)
        idx_h_end_in_text = min(len(lines_of_text), idx_h_end_in_text)

        if idx_h_start_in_text >= idx_h_end_in_text:
            print(f"{indent}[R_SPLIT_DEBUG] Heading split: Skipping empty segment for heading '{h['heading_text']}' at line {h['line_no']}.")
            continue

        sub_text_lines = lines_of_text[idx_h_start_in_text:idx_h_end_in_text]
        sub_text = "".join(sub_text_lines)

        if not sub_text.strip():
            print(f"{indent}[R_SPLIT_DEBUG] Heading split: Skipping effectively empty sub_text for heading '{h['heading_text']}' at line {h['line_no']}.")
            continue

        # Original bail out: if sub_text is the same as the input text, means no actual split is happening here.
        # This can occur if `text` consists only of the content under one of the `splits` headings.
        if sub_text == text and len(splits) == 1 : # only if it's the only split and it's the whole text
             print(f"{indent}[R_SPLIT_DEBUG] Heading split: sub_text is same as input text for heading '{h['heading_text']}'. This should have been caught by single heading guard. Returning as is.")
             # This case should ideally be handled by the "single heading at start_line" guard.
             # If it reaches here, it means the heading wasn't at the start of `text`.
             # We associate `h` as its heading.
             return [{ "text": text, "own_heading": h["heading_text"], "start_line": sub_start_abs, "end_line": sub_end_abs }]

        print(f"{indent}[R_SPLIT_DEBUG] Recursing on heading split for '{h['heading_text']}' (lines {sub_start_abs}-{sub_end_abs}): {log_snippet(sub_text.strip())}")
        sub_chunks = recursive_split_by_hierarchy_and_delimiters(
            sub_text, headings, # Pass all headings down, filtering happens at start of call
            sub_start_abs, sub_end_abs,
            max_tokens, _depth + 1
        )
        # The returned sub_chunks should ideally have their own_heading set correctly.
        # If a sub_chunk is returned and its `own_heading` is None, it means it's content under `h`.
        for sc in sub_chunks:
            if sc.get("own_heading") is None:
                sc["own_heading"] = h["heading_text"]
        chunks.extend(sub_chunks)

    final_chunk_snippets = [f"('{log_snippet(c['text'].strip())}', h='{c.get('own_heading')}', lines {c['start_line']}-{c['end_line']})" for c in chunks]
    print(f"{indent}[R_SPLIT_DEBUG] Returning {len(chunks)} chunks from heading-based splitting. Snippets: {final_chunk_snippets}")
    return chunks
