#!/usr/bin/env python3
import argparse
import os
import re
import sys
from typing import List, Tuple, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
    """
    chunks = []
    for i, (start, _) in enumerate(offsets):
        end = offsets[i+1][0] if i+1 < len(offsets) else len(full_text)
        chunks.append(full_text[start:end])
    return chunks

def tfidf_cosine_similarity(a: str, b: str) -> float:
    """
    Compute TF-IDF vectors for strings a and b, then return cosine similarity.
    If TF-IDF fails due to empty vocabulary, return 1.0 to force a merge.
    """
    try:
        vect = TfidfVectorizer().fit([a, b])
        vecs = vect.transform([a, b])
        return cosine_similarity(vecs[0], vecs[1])[0][0]
    except ValueError:
        return 1.0

def semimatch_and_merge_tfidf(chunks: List[str], threshold: float) -> List[str]:
    """
    Merge adjacent chunks if their TF-IDF cosine similarity exceeds threshold.
    """
    if not chunks:
        return []
    merged = []
    buffer = chunks[0]
    for nxt in chunks[1:]:
        sim = tfidf_cosine_similarity(buffer, nxt)
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
            slug = "full_document"
        chunk_text = text_no_code if not reintegrate_code else reinsert_code(text_no_code, code_map)
        return [(slug, chunk_text)]

    # 4) Naively split on offsets in code-free text
    naive_chunks_no_code = naive_split_on_offsets(text_no_code, offsets)

    # 5) Semantically merge adjacent code-free chunks
    merged_chunks_no_code = semimatch_and_merge_tfidf(naive_chunks_no_code, tfidf_threshold)

    # 6) Reinsert code if requested, derive slug for each merged chunk
    results: List[Tuple[str, str]] = []
    print(reintegrate_code)
    for chunk_no_code in merged_chunks_no_code:
        chunk_text = chunk_no_code if not reintegrate_code else reinsert_code(chunk_no_code, code_map)
        m = re.search(r'(?m)^#{1,' + str(chosen_level) + r'}\s+(.*)', chunk_no_code)
        if m:
            raw = m.group(1).strip()
            slug = slugify(raw)
        else:
            slug = f"topic_{len(results)+1}"
        results.append((slug, chunk_text))

    return results

def is_header_only_chunk(text: str) -> bool:
    """
    Return True if the chunk contains only a single heading and no other non-whitespace lines.
    """
    lines = [line for line in text.splitlines() if line.strip() != ""]
    if not lines:
        return True
    # If only one line, and it starts with '#', consider header-only
    if len(lines) == 1 and re.match(r'^\s*#+\s+', lines[0]):
        return True
    return False

def process_single_markdown_file(md_file_path: str, base_input_dir: str, args: argparse.Namespace):
    """
    Processes a single Markdown file: reads, splits into topics, and writes output,
    replicating the input directory structure relative to base_input_dir.
    """
    # md_file_path is expected to be absolute
    relative_path_to_file_dir = os.path.relpath(os.path.dirname(md_file_path), base_input_dir)
    filename_no_ext = os.path.splitext(os.path.basename(md_file_path))[0]

    if relative_path_to_file_dir == ".":
        file_specific_output_dir = os.path.join(args.output_dir, filename_no_ext)
    else:
        file_specific_output_dir = os.path.join(args.output_dir, relative_path_to_file_dir, filename_no_ext)

    print(f"Processing file: {md_file_path} -> into {file_specific_output_dir}")

    # 1) Read the full Markdown
    with open(md_file_path, "r", encoding="utf-8") as f:
        full_text = f.read()

    # 2) Split into topic chunks
    # Ensure split_into_topics and is_header_only_chunk are accessible (module level)
    topics = split_into_topics(
        full_text,
        min_heading_count=args.min_heading_count,
        max_split_level=args.max_split_level,
        tfidf_threshold=args.tfidf_threshold,
        reintegrate_code=args.reintegrate_code
    )

    # 3) Write each (slug, chunk_text) to output_dir, optionally dropping empty-header chunks
    # This will be refined in a later step to create subdirectories per input file if needed.
    os.makedirs(file_specific_output_dir, exist_ok=True)
    written = 0
    for slug, text in topics:
        if args.drop_empty_headers and is_header_only_chunk(text):
            continue
        filename = f"{slug}.md"
        # For now, all topic files go into the root of args.output_dir
        # Consider prefixing slug with md_file_path basename to avoid collisions if not handled by caller
        outpath = os.path.join(file_specific_output_dir, filename)
        with open(outpath, "w", encoding="utf-8") as outf:
            outf.write(text)
        written += 1

    print(f"Wrote {written} topic file(s) from '{md_file_path}' into '{file_specific_output_dir}'.")

def main():
    parser = argparse.ArgumentParser(
        description="Split a Markdown file or files in a directory into per-topic subfiles." # Updated description
    )
    parser.add_argument(
        "file_path",
        help="Path to the input Markdown file or a directory containing Markdown files." # Updated help
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="topics_output",
        help="Directory to write the topic subfiles (default: ./topics_output)."
    )
    parser.add_argument(
        "--min_heading_count",
        type=int,
        default=3,
        help="Minimum number of headings at chosen level to trigger splitting (default: 3)."
    )
    parser.add_argument(
        "--max_split_level",
        type=int,
        default=2,
        help="Maximum heading level to attempt splitting on (1=H1, 2=H2, etc., default=2)."
    )
    parser.add_argument(
        "--tfidf_threshold",
        type=float,
        default=0.9,
        help="TF-IDF cosine threshold to merge adjacent chunks (default: 0.9)."
    )
    parser.add_argument(
        "--reintegrate_code",
        action="store_true",
        default=True,
        help="Whether to reinsert fenced code into chunks (default: True)."
    )
    parser.add_argument(
        "--drop_empty_headers",
        action="store_true",
        default=True,
        help="If set, delete any chunk that contains only a header and no other content."
    )

    args = parser.parse_args()

    # Check if input is a file or directory
    if not os.path.exists(args.file_path):
        print(f"Error: Input path not found: {args.file_path}")
        sys.exit(1)

    if os.path.isfile(args.file_path):
        if not args.file_path.lower().endswith(".md"):
            print(f"Error: Input file '{args.file_path}' is not a Markdown file (.md).")
            sys.exit(1)
        print(f"Input is a single Markdown file: {args.file_path}")
        abs_md_file_path = os.path.abspath(args.file_path)
        base_input_dir_for_relpath = os.path.dirname(abs_md_file_path)
        process_single_markdown_file(abs_md_file_path, base_input_dir_for_relpath, args)

    elif os.path.isdir(args.file_path):
        print(f"Input is a directory: {args.file_path}")
        print(f"Scanning directory '{os.path.abspath(args.file_path)}' for Markdown files...") # New message
        markdown_files_to_process = []
        base_input_dir = os.path.abspath(args.file_path)
        for root, dirs, files in os.walk(base_input_dir): # Use absolute path for os.walk
            for file in files:
                if file.lower().endswith(".md"):
                    # os.path.join will correctly join root (already absolute) and file
                    markdown_files_to_process.append(os.path.join(root, file))

        if not markdown_files_to_process:
            print(f"No Markdown files (.md) found in directory: {args.file_path}")
        else:
            print(f"Found {len(markdown_files_to_process)} Markdown files to process:")
            for md_file_path_item_for_listing in markdown_files_to_process: # Use a different var name for clarity
                print(f"  - {md_file_path_item_for_listing}")

            print(f"\nStarting to process {len(markdown_files_to_process)} identified Markdown file(s)...") # New message
            for md_file_path_item in markdown_files_to_process:
                # md_file_path_item is already absolute here due to os.walk on absolute base_input_dir
                # print(f"  Processing: {md_file_path_item}") # This level of detail might be too much now
                try:
                    # Pass the absolute path of the item and the absolute base_input_dir
                    process_single_markdown_file(md_file_path_item, base_input_dir, args)
                except Exception as e:
                    print(f"Error processing file {md_file_path_item}: {e}")
                    # Continue with other files
            print(f"Finished processing all files in directory.")

    else:
        print(f"Error: Input path '{args.file_path}' is not a valid file or directory.")
        sys.exit(1)

    # The previous placeholder print is removed as processing is now invoked.

if __name__ == "__main__":
    main()

