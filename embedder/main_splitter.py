#!/usr/bin/env python3
"""
Processes Markdown files to split them into topic-based segments,
then further chunks these topics into smaller pieces suitable for embedding.
Includes functionality for initial topic splitting based on headings and TF-IDF similarity,
recursive chunking of topics by hierarchy and delimiters, metadata extraction,
and optional merging of final small chunk files.
"""
import argparse
import os
import re
import sys
from typing import List, Dict, Tuple
from pathlib import Path # Added Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Helper functions from Marking_splitter (for hierarchical chunking)
# and metadata_parser (for extracting metadata elements) are imported.
# Topic splitting utilities formerly in File_to_topic.py are now part of this file.

from Marking_splitter import (
    count_tokens,
    recursive_split_by_hierarchy_and_delimiters
)
from metadata_parser import (
    extract_description,
    parse_version_context,
    parse_outline_date,
    extract_headings,
    get_headings_only,
    extract_keywords
)

# --- Configuration defaults ---
DEFAULT_CHUNK_SIZE = 1200      # max tokens per chunk
LOWER_THRESHOLD = 500          # min tokens to consider merging small chunks
MERGE_THRESHOLD = 0.3          # cosine-sim threshold for merging siblings


# --- Topic Splitting Utilities (copied from File_to_topic.py) ---

def slugify(text: str) -> str:
    """
    Simplest slugifier: lowercase, replace non-alphanumeric with underscore,
    collapse multiple underscores, strip leading/trailing underscores.
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    text = re.sub(r'__+', '_', text)
    return text.strip('_')

def extract_fenced_code(full_text: str) -> Tuple[str, Dict[str, str]]:
    # Pattern to capture the code block (group 1) and the immediately following newline(s) (group 2)
    code_pattern = re.compile(r'(?ms)(```.*?```)(\n?)')
    code_map: Dict[str, str] = {}
    idx = 0

    current_search_start_pos = 0
    accumulated_parts = []
    temp_processed_text_for_searching = full_text # Keep original full_text for searching

    while True:
        match = code_pattern.search(temp_processed_text_for_searching, pos=current_search_start_pos)

        if not match:
            # No more matches, append the rest of the text from current_search_start_pos
            accumulated_parts.append(temp_processed_text_for_searching[current_search_start_pos:])
            break

        block_content_for_map = match.group(1)  # The ```...``` content itself
        captured_newline = match.group(2)     # The captured newline(s) or empty string after the block

        key = f"__CODE{idx}__"

        match_start_offset, match_end_offset = match.span(0) # Span of the entire match (block + newline)

        # Append the part of the text *before* the current match
        accumulated_parts.append(temp_processed_text_for_searching[current_search_start_pos:match_start_offset])

        # Add the placeholder followed by the captured newline(s)
        # This preserves the original spacing after the code block.
        accumulated_parts.append(key + captured_newline)
        code_map[key] = block_content_for_map

        # Move the search start position to the end of the current match
        current_search_start_pos = match_end_offset
        idx += 1

    return "".join(accumulated_parts), code_map

def reinsert_code(chunk: str, code_map: Dict[str, str]) -> str:
    """
    Given a chunk that may contain placeholders __CODEi__,
    replace each placeholder with its original fenced code block.
    """
    for key, code in code_map.items():
        chunk = chunk.replace(key, code)
    return chunk

def find_headings_at_level(full_text: str, level: int) -> List[Tuple[int, str]]:
    """
    Find all headings of exactly the specified Markdown level (e.g. level=1 matches '^# ').
    Returns a list of (byte_offset, heading_text).
    (Copied from File_to_topic.py)
    """
    pattern = re.compile(rf'(?m)^(#{{{level}}})\s+(.*)')
    matches = []
    for m in pattern.finditer(full_text):
        offset = m.start()
        heading_text = m.group(2).strip()
        matches.append((offset, heading_text))
    return matches

def naive_split_on_offsets(full_text: str, offsets: List[Tuple[int, str]]) -> List[str]:
    """
    Given full_text and a list of (offset, heading_text) sorted by offset,
    return a list of substrings, each from one offset to the next.
    Each substring begins with its heading.
    (Copied from File_to_topic.py)
    """
    chunks = []
    for i, (start, _) in enumerate(offsets):
        end = offsets[i+1][0] if i+1 < len(offsets) else len(full_text)
        chunks.append(full_text[start:end])
    return chunks

def _local_tfidf_cosine_similarity(a: str, b: str) -> float:
    """
    Compute TF-IDF vectors for strings a and b, then return cosine similarity.
    If TF-IDF fails due to empty vocabulary, return 1.0 to force a merge.
    (Copied and renamed from File_to_topic.py's tfidf_cosine_similarity)
    Uses TfidfVectorizer and cosine_similarity already imported in main_splitter.py.
    """
    try:
        # Ensure TfidfVectorizer and cosine_similarity are available in this scope
        # They are imported at the top of main_splitter.py
        vect = TfidfVectorizer().fit([a, b]) #fixed: true -> [a,b]
        vecs = vect.transform([a, b]) #fixed: true -> [a,b]
        return cosine_similarity(vecs[0], vecs[1])[0][0]
    except ValueError: # Typically "empty vocabulary"
        return 1.0 # Force merge if TF-IDF fails (e.g., very short, non-alphanumeric strings)

def semimatch_and_merge_tfidf(chunks: List[str], threshold: float) -> List[str]:
    """
    Merge adjacent chunks if their TF-IDF cosine similarity exceeds threshold.
    Uses _local_tfidf_cosine_similarity.
    (Copied from File_to_topic.py)
    """
    if not chunks:
        return []
    merged = []
    buffer = chunks[0]
    for nxt in chunks[1:]:
        sim = _local_tfidf_cosine_similarity(buffer, nxt)
        if sim > threshold:
            buffer = buffer + "\n\n" + nxt
        else:
            merged.append(buffer)
            buffer = nxt
    merged.append(buffer)
    return merged

def split_into_topics(
    full_text: str,
    min_heading_count: int,
    max_split_level: int,
    tfidf_threshold: float,
    reintegrate_code: bool
) -> List[Tuple[str, str]]:
    """
    1) Extract and remove fenced code blocks.
    2) Find headings at levels 1..max_split_level; if at least min_heading_count found,
       split on that level. Otherwise, treat entire text as one chunk.
    3) Naively split on chosen headings (in code-free text).
    4) Semantically merge adjacent chunks via TF-IDF.
    5) Optionally reinsert code placeholders into each merged chunk.
    6) Return list of (slug, chunk_text).
    (Copied from File_to_topic.py)
    """
    # 1) Extract code
    text_no_code, code_map = extract_fenced_code(full_text)

    # 2) Find headings up to max_split_level
    chosen_level = None
    offsets: List[Tuple[int, str]] = []
    for level in range(1, max_split_level + 1):
        headings = find_headings_at_level(text_no_code, level)
        if len(headings) >= min_heading_count:
            chosen_level = level
            offsets = headings
            break

    # 3) If no splitting level found, entire document is one topic
    if chosen_level is None:
        m = re.search(r'(?m)^#\s+(.*)', text_no_code)
        if m:
            raw_heading = m.group(1).strip()
            slug = slugify(raw_heading)
        else:
            # Try to find the filename if possible, or a generic slug
            # This part is tricky as we don't have filename here directly.
            # Fallback to a generic slug.
            slug = "full_document_topic" # Make it more specific
        chunk_text = text_no_code if not reintegrate_code else reinsert_code(text_no_code, code_map)
        return [(slug, chunk_text)]

    # 4) Naively split on offsets in code-free text
    naive_chunks_no_code = naive_split_on_offsets(text_no_code, offsets)

    # 5) Semantically merge adjacent code-free chunks
    merged_chunks_no_code = semimatch_and_merge_tfidf(naive_chunks_no_code, tfidf_threshold)

    # 6) Reinsert code if requested, derive slug for each merged chunk
    results: List[Tuple[str, str]] = []
    # print(f"[DEBUG] Reintegrate code flag in split_into_topics: {reintegrate_code}") # For debugging
    for chunk_no_code in merged_chunks_no_code:
        chunk_text = chunk_no_code # Default to no code reintegration
        if reintegrate_code:
             chunk_text = reinsert_code(chunk_no_code, code_map)

        # Try to find heading within the chunk_no_code (as code might interfere with regex)
        # Search for chosen_level first, then any higher level up to H1.
        best_heading_for_slug = None
        for lvl_search in range(chosen_level, 0, -1):
            m_slug = re.search(rf'(?m)^(#{{{lvl_search}}})\s+(.*)', chunk_no_code)
            if m_slug:
                best_heading_for_slug = m_slug.group(2).strip()
                break

        if best_heading_for_slug:
            slug = slugify(best_heading_for_slug)
        else:
            # Fallback slug if no heading found in chunk (should be rare if split by headings)
            slug = f"topic_{len(results)+1}"
        results.append((slug, chunk_text))

    return results

def is_header_only_chunk(text: str) -> bool:
    """
    Return True if the chunk contains only a single heading and no other non-whitespace lines.
    (Moved from File_to_topic.py)
    """
    lines = [line for line in text.splitlines() if line.strip() != ""]
    if not lines:
        return True # Empty or whitespace-only is effectively header-only for dropping purposes
    # If only one line, and it starts with '#', consider header-only
    if len(lines) == 1 and re.match(r'^\s*#+\s+', lines[0]):
        return True
    return False

# --- End of Topic Splitting Utilities ---


def find_deepest_chunk_directories(root_output_dir: str) -> List[str]:
    """
    Finds all directories within the root_output_dir that contain .md files
    but no further subdirectories. These are considered the "deepest" directories
    where actual chunk files reside.
    """
    deepest_dirs: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root_output_dir):
        has_md_files = any(f.lower().endswith(".md") for f in filenames)
        is_deepest = not dirnames  # No subdirectories

        if has_md_files and is_deepest:
            deepest_dirs.append(dirpath)
    return deepest_dirs


MERGE_LOG_PREFIX = "[MERGE_LOG]"

def _extract_frontmatter_and_content(file_path: str) -> Tuple[str, str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"{MERGE_LOG_PREFIX} Error reading file {file_path}: {e}")
        return "", ""

    if not lines or lines[0].strip() != '---':
        # No frontmatter or not starting with ---
        return "", "".join(lines)

    frontmatter_end_index = -1
    for i, line in enumerate(lines[1:]): # Start searching from the second line
        if line.strip() == '---':
            frontmatter_end_index = i + 1 # index in original lines list
            break

    if frontmatter_end_index != -1:
        frontmatter = "".join(lines[:frontmatter_end_index + 1]) # Include the closing ---
        content = "".join(lines[frontmatter_end_index + 1:])
        return frontmatter, content
    else:
        # Opening --- but no closing ---, treat all as content
        print(f"{MERGE_LOG_PREFIX} Warning: File {file_path} has opening '---' but no closing '---'. Treating all as content.")
        return "", "".join(lines)


def merge_files_in_directory(directory_path: str, max_tokens_per_merged_file: int):
    print(f"{MERGE_LOG_PREFIX} Starting to process directory: {directory_path}")
    try:
        all_files_in_dir = os.listdir(directory_path)
    except FileNotFoundError:
        print(f"{MERGE_LOG_PREFIX} Error: Directory not found: {directory_path}")
        return
    except Exception as e:
        print(f"{MERGE_LOG_PREFIX} Error listing files in directory {directory_path}: {e}")
        return

    md_files = sorted([f for f in all_files_in_dir if f.lower().endswith(".md")])

    if not md_files:
        print(f"{MERGE_LOG_PREFIX} No .md files found in {directory_path}.")
        return

    print(f"{MERGE_LOG_PREFIX} Found {len(md_files)} .md files in {directory_path}.")

    # Convert to full paths
    md_file_paths = [os.path.join(directory_path, f) for f in md_files]

    processed_files_for_current_run = set() # Tracks files already part of a merge OR processed as a standalone first file

    for i, first_file_path in enumerate(md_file_paths):
        if first_file_path in processed_files_for_current_run:
            continue

        print(f"{MERGE_LOG_PREFIX} Starting new potential merged file with: {os.path.basename(first_file_path)}")

        first_file_frontmatter, first_file_body = _extract_frontmatter_and_content(first_file_path)

        if not first_file_frontmatter and first_file_body.strip().startswith("---"):
             # This case can happen if _extract_frontmatter_and_content returns "" for frontmatter
             # because the file *only* contained frontmatter, or started with --- but had no closing ---.
             # For a file to be the base of a merge, it should ideally have valid frontmatter.
             # If first_file_frontmatter is empty, but the body starts with '---', it's likely malformed.
             # For now, we will use a minimal default frontmatter if the extracted one is empty.
            print(f"{MERGE_LOG_PREFIX} Warning: File {os.path.basename(first_file_path)} has no valid frontmatter for merging. Using minimal default.")
            # Minimal valid frontmatter, e.g. if title was expected.
            # This part might need more sophisticated handling based on expected frontmatter fields.
            default_title = os.path.splitext(os.path.basename(first_file_path))[0]
            first_file_frontmatter = f"---\ntitle: {default_title} (merged)\n---\n"
            # The body is kept as is, if _extract_frontmatter_and_content put everything in body.

        current_merged_content_parts = [first_file_body.strip()]
        current_token_count = count_tokens(first_file_body)

        files_in_current_merge_sequence = [first_file_path]

        # Try to add subsequent files
        for next_file_path in md_file_paths[i+1:]:
            if next_file_path in processed_files_for_current_run:
                continue

            _unused_frontmatter, next_file_body = _extract_frontmatter_and_content(next_file_path)
            tokens_in_next_file = count_tokens(next_file_body)

            if current_token_count + tokens_in_next_file <= max_tokens_per_merged_file:
                current_merged_content_parts.append(next_file_body.strip())
                current_token_count += tokens_in_next_file
                files_in_current_merge_sequence.append(next_file_path)
                print(f"{MERGE_LOG_PREFIX} Added {os.path.basename(next_file_path)} to merge sequence starting with {os.path.basename(first_file_path)}")
            else:
                # Cannot add this file, so stop trying for the current merge sequence
                break

        # Finalize and Write Merged File (always rewrite the first file of the sequence)
        merged_filename = os.path.basename(first_file_path)
        output_path = first_file_path # Overwrite the first file

        # Ensure frontmatter ends with a newline
        if first_file_frontmatter and not first_file_frontmatter.endswith('\n'):
            first_file_frontmatter += '\n'

        # Join parts with double newline.
        # The problem description mentioned "\n\n---\n\n" as a potential separator.
        # Using just "\n\n" between markdown bodies. If a visual separator is desired,
        # it should be explicitly added here.
        merged_body_content = "\n\n".join(current_merged_content_parts)
        final_merged_text = first_file_frontmatter + merged_body_content

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_merged_text)
            print(f"{MERGE_LOG_PREFIX} Written merged file: {merged_filename} ({len(files_in_current_merge_sequence)} files, {current_token_count} tokens)")
        except Exception as e:
            print(f"{MERGE_LOG_PREFIX} Error writing merged file {output_path}: {e}")
            # If writing fails, we should not mark files for deletion or as processed
            continue

        # Mark all files in this sequence (including the first one) as processed for this run
        for fp in files_in_current_merge_sequence:
            processed_files_for_current_run.add(fp)

        # Delete the other original files that were merged into the first file
        if len(files_in_current_merge_sequence) > 1:
            for file_to_delete_path in files_in_current_merge_sequence[1:]:
                try:
                    os.remove(file_to_delete_path)
                    print(f"{MERGE_LOG_PREFIX} Deleted original file: {os.path.basename(file_to_delete_path)}")
                except Exception as e:
                    print(f"{MERGE_LOG_PREFIX} Error deleting file {os.path.basename(file_to_delete_path)}: {e}")

    print(f"{MERGE_LOG_PREFIX} Finished processing directory: {directory_path}")


def process_topic_text(
    topic_slug: str,
    topic_text: str,
    original_filename: str,
    mode: str,
    chunk_size: int,
    lower_threshold: int,
    merge_threshold: float,
    use_llm_stoplist: bool,
    output_dir: str,
    drop_empty_headers: bool
) -> List[Dict]:
    """
    Processes a single topic's text content. This involves:
    - Extracting file-level metadata (hardcoded cluster, version context, outline date from topic text).
    - Identifying the root title of the topic.
    - Preparing for custom stop words if LLM stoplist generation is enabled (currently placeholder).
    - Extracting all headings from the topic text.
    - Recursively splitting the topic text into smaller chunks based on heading hierarchy and token limits.
    - For each chunk:
        - Determining its own heading.
        - Calculating a section number.
        - Generating a unique chunk ID (incorporating topic slug and start line).
        - Building a section hierarchy.
        - Extracting keywords and a description.
        - Assembling all metadata.
        - If in "md" mode, writing the chunk text and metadata to a .md file.
        - If in "embed" mode, adding the chunk text and metadata to a list for return.
    - Optionally, if in "embed" mode, merging very small sibling chunks based on token count and similarity.

    Args:
        topic_slug: The slugified name of the current topic.
        topic_text: The actual text content of the current topic.
        original_filename: The relative path of the original source Markdown file (used for metadata).
        mode: "md" to write chunked .md files, or "embed" to return text+metadata dictionaries.
        chunk_size: Maximum tokens per final chunk from hierarchical splitting.
        lower_threshold: (For "embed" mode) Min tokens to consider merging small final chunks.
        merge_threshold: (For "embed" mode) Cosine similarity for merging small final chunks.
        use_llm_stoplist: Flag to enable LLM-based stoplist generation (currently placeholder).
        output_dir: The directory where final chunked .md files for this topic should be written.
        drop_empty_headers: If True, skip writing chunks that are only a header.

    Returns:
        List[Dict]: A list of {"text": chunk_text, "metadata": chunk_metadata} dictionaries if mode is "embed".
                     An empty list if mode is "md" (as files are written to disk).
    """
    # 1) File-level metadata
    cluster = "memory" # Hardcoded for now, consider making this configurable or derived
    topic = topic_slug # This is the slug of the current topic segment

    # Parse version context and outline date from the current topic's text
    version_context = parse_version_context(topic_text)
    outline_date = parse_outline_date(topic_text)

    # 'original_filename' is the relative path of the original large Markdown file being processed.
    # This is used for the 'file_path' field in metadata.
    file_path = original_filename

    # 2) Root-level title (first H1 found in the current topic_text)
    # This might be different from the original file's first H1 if split by H1s.
    root_title = None
    for line in topic_text.splitlines():
        if line.startswith("# "):
            root_title = line[2:].strip()
            break

    # 3) Optional LLM stoplist generation
    custom_stop: List[str] = []
    if use_llm_stoplist:
        try:
            # Placeholder for actual LLM-based stoplist generation.
            # This would populate `custom_stop` with words.
            raise NotImplementedError("LLM-based stoplist generation is not implemented.")
        except NotImplementedError:
            # If not implemented or fails, custom_stop remains empty.
            # extract_keywords will then use its default stoplist.
            print("[INFO] LLM-based stoplist not implemented; using default stoplist for keyword extraction.")
            custom_stop = []

    # 4) Extract all headings (levels 2–6) from the current topic_text
    headings = extract_headings(topic_text)

    # 5) Identify top-level sections by Level-2 headings in topic_text
    level2 = [h for h in headings if h["level"] == 2]
    boundaries = [{"line_no": 0, "section_number": None, "heading_text": root_title}]
    boundaries += level2
    boundaries.append({"line_no": len(topic_text.splitlines()), "section_number": None})

    # 6) If in "md" mode, ensure output_dir exists
    if mode == "md":
        os.makedirs(output_dir, exist_ok=True)

    chunks_out: List[Dict] = []
    last_chunk_title = root_title

    # 7) Process each top-level section within the topic_text
    all_lines = topic_text.splitlines()
    for i in range(len(boundaries) - 1):
        sec_start = boundaries[i]["line_no"]
        sec_end = boundaries[i+1]["line_no"]
        section_lines = all_lines[sec_start:sec_end]
        section_text = "\n".join(section_lines)

        # 7a) Recursively split by hierarchy and delimiters
        section_chunks = recursive_split_by_hierarchy_and_delimiters(
            section_text,
            headings,
            sec_start,
            sec_end,
            chunk_size
        )

        for chunk in section_chunks:
            text = chunk["text"]
            # Diagnostic print
            # print(f"[PROCESS_TOPIC_DEBUG] Processing chunk. Title hint: {chunk.get('own_heading', 'N/A')}. Text length: {len(text)}. Text snippet: {text[:200]}...{text[-100:] if len(text) > 300 else ''}")

            # Small chunk filtering
            # if count_tokens(text) < 5:
            #     # print(f"[PROCESS_TOPIC_DEBUG] Skipping chunk with token count < 5. Title hint: {chunk.get('own_heading', 'N/A')}. Token count: {count_tokens(text)}.")
            #     continue

            # 7b) Determine own_heading (first H2..H6 in chunk or inherited)
            local_headings = get_headings_only(text)
            if not local_headings:
                own_heading = last_chunk_title
            elif len(local_headings) == 1:
                own_heading = local_headings[0]
            else:
                if last_chunk_title in local_headings:
                    idx = local_headings.index(last_chunk_title)
                    if idx + 1 < len(local_headings):
                        own_heading = local_headings[idx + 1]
                    else:
                        own_heading = local_headings[idx]
                else:
                    own_heading = local_headings[0]
            last_chunk_title = own_heading

            # 7c) Determine section_number: reuse if present else synthetic
            sec_num = None
            for h in headings:
                if h["heading_text"] == own_heading and h["line_no"] <= chunk["start_line"]:
                    sec_num = h["section_number"]
                    break
            if sec_num is None:
                prev_nums = [int(x) for x in last_chunk_title.split(".") if x.isdigit()]
                if prev_nums:
                    prev_nums[-1] += 1
                    sec_num = ".".join(str(x) for x in prev_nums)
                else:
                    sec_num = "1"
            # Modified chunk_id to include start line
            chunk_id = f"{cluster}_{topic}_sec{sec_num}_L{chunk['start_line']}"

            # 7d) Build section_hierarchy from headings appearing before this chunk
            ancestors = [h["heading_text"] for h in headings if h["line_no"] <= chunk["start_line"]]
            section_hierarchy = ancestors

            # 7e) Keywords and description
            keywords = extract_keywords(text, custom_stop)
            description = extract_description(text)

            # Ensure metadata uses the new unique chunk_id
            metadata = {
                "id": chunk_id, # Updated chunk_id
                "cluster": cluster,
                "topic": topic,
                "title": own_heading,
                "version_context": version_context,
                "outline_date": outline_date,
                "section_hierarchy": section_hierarchy,
                "keywords": keywords,
                "description": description,
                "file_path": file_path
            }

            # 8) Optionally drop header-only chunks in md mode
            if mode == "md" and drop_empty_headers:
                lines_nonempty = [ln for ln in text.splitlines() if ln.strip()]
                if len(lines_nonempty) == 1 and re.match(r'^\s*#+\s+', lines_nonempty[0]):
                    continue

            if mode == "md":
                chunk_filename = os.path.join(output_dir, f"{chunk_id}.md")
                with open(chunk_filename, "w", encoding="utf-8") as cf:
                    cf.write("---\n")
                    for k, v in metadata.items():
                        cf.write(f"{k}: {v}\n")
                    cf.write("---\n\n")
                    cf.write(text)
            else:
                chunks_out.append({"text": text, "metadata": metadata})

    # 9) Optional merge of tiny sibling chunks (only in "embed" mode)
    if mode == "embed" and lower_threshold and merge_threshold:
        merged: List[Dict] = []
        i = 0
        while i < len(chunks_out):
            curr = chunks_out[i]
            curr_tokens = count_tokens(curr["text"])
            if curr_tokens < lower_threshold and i + 1 < len(chunks_out):
                nxt = chunks_out[i+1]
                nxt_tokens = count_tokens(nxt["text"])
                if (
                    nxt_tokens < lower_threshold and
                    curr["metadata"]["section_hierarchy"] == nxt["metadata"]["section_hierarchy"]
                ):
                    vecs = TfidfVectorizer().fit_transform([curr["text"], nxt["text"]])
                    sim = cosine_similarity(vecs[0], vecs[1])[0][0]
                    if sim >= merge_threshold:
                        merged_text = curr["text"] + "\n\n" + nxt["text"]
                        merged_meta = curr["metadata"]
                        merged_meta["description"] = extract_description(merged_text)
                        merged_meta["keywords"] = extract_keywords(merged_text, custom_stop)
                        merged_meta["id"] = curr["metadata"]["id"]
                        merged.append({"text": merged_text, "metadata": merged_meta})
                        i += 2
                        continue
            merged.append(curr)
            i += 1
        return merged

    return chunks_out


def unified_main():
    parser = argparse.ArgumentParser(
        description="Recursively split all Markdown files in a folder into topics (TF-IDF), then chunk them with metadata."
    )
    parser.add_argument(
        "input_path",
        help="Path to a Markdown file or a directory of Markdown files."
    )
    parser.add_argument(
        "--mode",
        choices=["embed", "md"],
        default="md",
        help="embed: return text+metadata; md: write final chunked .md files."
    )
    parser.add_argument(
        "--min_heading_count",
        type=int,
        default=3, # From File_to_topic.py
        help="Minimum number of headings at chosen level to trigger topic splitting (default: 3)."
    )
    parser.add_argument(
        "--max_split_level",
        type=int,
        default=2, # From File_to_topic.py
        help="Maximum heading level to attempt splitting topics on (1=H1, 2=H2, etc., default=2)."
    )
    parser.add_argument(
        "--tfidf_threshold", # This is for initial topic splitting
        type=float,
        default=0.9, # From File_to_topic.py
        help="TF-IDF cosine threshold to merge adjacent topic chunks during initial topic splitting (default: 0.9)."
    )
    parser.add_argument(
        "--chunk_size", # For hierarchical splitting of topics into chunks
        type=int,
        default=DEFAULT_CHUNK_SIZE, # This is 1200
        help="Max tokens per final chunk during hierarchical splitting (default: 1200)."
    )
    parser.add_argument(
        "--lower_threshold", # For final, optional chunk merging
        type=int,
        default=LOWER_THRESHOLD, # This is 500
        help="Min tokens to consider merging small final chunks if --merge_chunks is enabled (default: 500)."
    )
    parser.add_argument(
        "--merge_threshold", # For final, optional chunk merging (similarity)
        type=float,
        default=MERGE_THRESHOLD, # This is 0.3
        help="Cosine similarity threshold for merging adjacent small final chunks if --merge_chunks is enabled (default: 0.3)."
    )
    parser.add_argument(
        "--use_llm_stoplist",
        action="store_true",
        help="Flag to generate a stoplist via LLM (not implemented)."
    )
    parser.add_argument(
        "--reintegrate_code",
        action="store_true",
        default=True,
        help="Whether to reinsert fenced code into topic subchunks (default: True)."
    )
    parser.add_argument(
        "--drop_empty_headers",
        action="store_true",
        default=False, # Keep this default from main_splitter.py
        help="If set, skip writing any final chunk that is only a header (default: False)."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="final_output",
        help="Directory to write final chunked .md files (default: ./final_output)."
    )
    parser.add_argument(
        "--save_intermediate_topics",
        action="store_true",
        default=False,
        help="If set, save the intermediate topic files to disk (default: False, process in memory)."
    )
    parser.add_argument(
        "--merge_chunks",
        action="store_true",
        default=True,
        help="Enable merging of small chunk files in the deepest subdirectories."
    )
    parser.add_argument(
        "--max_merged_chunk_tokens", # For final, optional chunk merging
        type=int,
        default=1200,
        help="Maximum token count for a merged chunk file if --merge_chunks is enabled (default: 1200)."
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        print(f"Error: Path not found: {args.input_path}")
        sys.exit(1)

    # Gather Markdown files from input path
    md_files: List[str] = []
    if os.path.isdir(args.input_path):
        print(f"Input is a directory, scanning for .md topic files in: {os.path.abspath(args.input_path)}")
        for root, _, files in os.walk(args.input_path):
            for file in files:
                if file.lower().endswith(".md"):
                    md_files.append(os.path.join(root, file))
        if not md_files:
            print(f"No .md files found in directory {args.input_path}")
            sys.exit(0) # Or handle as appropriate
        print(f"Found {len(md_files)} .md files to process:")
        for f_path in md_files:
            print(f"  - {f_path}")

    elif os.path.isfile(args.input_path):
        if not args.input_path.lower().endswith(".md"):
            print(f"Error: Input file '{args.input_path}' is not a Markdown file (.md).")
            sys.exit(1)
        print(f"Input is a single .md topic file: {args.input_path}")
        md_files.append(args.input_path)
    else:
        print(f"Error: Input path '{args.input_path}' is not a valid file or directory.")
        sys.exit(1)


    total_written = 0
    # total_topics_processed = 0 # Or just use len(md_files) later
    # The 'total_written' will now count actual final chunks if mode=='md',
    # or embeddable data items if mode=='embed'.
    # It will be incremented inside the topic loop.
    processed_items_count = 0


    for current_md_path_abs in md_files: # md_path is already absolute from earlier logic
        print(f"\n--- Processing source file: {current_md_path_abs} ---")

        try:
            with open(current_md_path_abs, "r", encoding="utf-8") as f:
                full_file_content = f.read()
        except Exception as e:
            print(f"Error reading source file {current_md_path_abs}: {e}")
            continue # Skip to next file

        # Call split_into_topics (now part of this file)
        topics_data = split_into_topics(
            full_file_content,
            min_heading_count=args.min_heading_count,
            max_split_level=args.max_split_level,
            tfidf_threshold=args.tfidf_threshold, # This is for topic merging
            reintegrate_code=args.reintegrate_code
        )

        # Determine base input directory for relative path calculations
        if os.path.isdir(args.input_path):
            base_input_for_relpath = os.path.abspath(args.input_path)
        else: # Single file input
            base_input_for_relpath = os.path.dirname(os.path.abspath(args.input_path))

        # Relative path of the original MD file (directory part)
        relative_dir_of_original_md = os.path.relpath(os.path.dirname(current_md_path_abs), base_input_for_relpath)
        if relative_dir_of_original_md == ".":
            relative_dir_of_original_md = "" # Avoids './' in path for cleaner output paths

        original_md_filename_base = os.path.splitext(os.path.basename(current_md_path_abs))[0]
        original_md_filename_slug = slugify(original_md_filename_base) # Use the slugify function now in this file

        # Path for saving intermediate topics (if enabled)
        # Using Path object for cleaner path construction
        intermediate_topics_base_dir = Path(args.output_dir + "_topics_intermediate")

        if args.save_intermediate_topics:
            current_intermediate_topic_dir = intermediate_topics_base_dir / relative_dir_of_original_md / original_md_filename_slug
            os.makedirs(current_intermediate_topic_dir, exist_ok=True)
            print(f"[INFO] Saving {len(topics_data)} intermediate topics for '{current_md_path_abs}' to '{current_intermediate_topic_dir}'")
            for topic_slug_val, topic_text_val in topics_data:
                try:
                    with open(current_intermediate_topic_dir / f"{topic_slug_val}.md", "w", encoding="utf-8") as tf:
                        tf.write(topic_text_val)
                except Exception as e:
                     print(f"Error writing intermediate topic file {topic_slug_val}.md: {e}")

        print(f"Processing {len(topics_data)} topics from file: {current_md_path_abs}")
        for topic_slug_val, topic_text_val in topics_data:
            output_dir_for_this_topic_chunks = Path(args.output_dir) / relative_dir_of_original_md / original_md_filename_slug / topic_slug_val
            os.makedirs(output_dir_for_this_topic_chunks, exist_ok=True)

            path_for_metadata = os.path.relpath(current_md_path_abs, base_input_for_relpath)

            # Call process_topic_text
            final_chunks_data_for_topic = process_topic_text(
                topic_slug=topic_slug_val,
                topic_text=topic_text_val,
                original_filename=path_for_metadata,
                mode=args.mode,
                chunk_size=args.chunk_size,
                lower_threshold=args.lower_threshold, # For final chunk merging in process_topic_text (if mode=embed)
                merge_threshold=args.merge_threshold,   # For final chunk merging in process_topic_text (if mode=embed)
                use_llm_stoplist=args.use_llm_stoplist, # This arg seems unused in process_topic_text
                output_dir=str(output_dir_for_this_topic_chunks),
                drop_empty_headers=args.drop_empty_headers
            )

            if args.mode == "md":
                # process_topic_text writes files directly. We need to count them if we want total_written.
                # For simplicity, let's count how many files were created in output_dir_for_this_topic_chunks
                try:
                    if os.path.exists(output_dir_for_this_topic_chunks):
                         processed_items_count += len(os.listdir(output_dir_for_this_topic_chunks))
                except Exception as e:
                    print(f"Error counting files in {output_dir_for_this_topic_chunks}: {e}")
            else: # mode == "embed"
                 processed_items_count += len(final_chunks_data_for_topic)


    # Update final summary prints
    if args.mode == "md":
        print(f"\nTotal final Markdown chunk files written: {processed_items_count} under base directory '{args.output_dir}'.")
    else: # mode == "embed"
        print(f"\nTotal embedded chunks generated: {total_written} from {len(md_files)} topic files.")

    # --- Optional Chunk Merging Process ---
    if args.mode == "md" and args.merge_chunks:
        print(f"\n--- Starting Chunk Merging Process ---")
        print(f"Scanning for deepest chunk directories in: {args.output_dir}")

        deepest_dirs_to_merge = find_deepest_chunk_directories(args.output_dir)

        if not deepest_dirs_to_merge:
            print("No deepest directories found containing .md files to merge.")
        else:
            print(f"Found {len(deepest_dirs_to_merge)} directories to process for merging.")
            # Note: The following counts are not implemented as merge_files_in_directory does not return them yet.
            # merged_files_count_total = 0
            # deleted_files_count_total = 0

            for dir_to_process in deepest_dirs_to_merge:
                # merge_files_in_directory prints its own logs using MERGE_LOG_PREFIX
                merge_files_in_directory(dir_to_process, args.max_merged_chunk_tokens)

            print(f"\n--- Chunk Merging Process Completed ---")
            # A more detailed summary could be added here if merge_files_in_directory returned statistics.
            # For now, users should check the [MERGE_LOG] entries.
            print(f"Please check '{MERGE_LOG_PREFIX}' logs above for details on merged files and deletions.")
            print(f"The number of files in '{args.output_dir}' may have changed due to merging.")


if __name__ == "__main__":
    unified_main()

