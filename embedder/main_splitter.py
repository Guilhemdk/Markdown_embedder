#!/usr/bin/env python3
import argparse
import os
import re
import sys
from typing import List, Dict, Tuple # Added Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import functions from the separate modules:
# – split_into_topics from Marking_splitter
# – recursive_split_by_hierarchy_and_delimiters and count_tokens from Marking_splitter
# – metadata helpers from metadata_parser
#
# Since these modules are provided alongside, we assume they're in the same directory.
from File_to_topic import (
        split_into_topics,
    is_header_only_chunk
)
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
    Given a single topic (slug, text) extracted by split_into_topics, perform
    the usual recursive chunking + metadata extraction. Writes .md files if mode=="md",
    or returns a list of {"text":..., "metadata":...} if mode=="embed".
    """
    # 1) File-level metadata: cluster is "memory" (hardcoded for these three files)
    cluster = "memory"
    topic = topic_slug
    version_context = parse_version_context(topic_text)
    outline_date = parse_outline_date(topic_text)
    # original_filename is now the relative path to the topic file itself.
    file_path = original_filename

    # 2) Root-level title (first H1 in topic_text)
    root_title = None
    for line in topic_text.splitlines():
        if line.startswith("# "):
            root_title = line[2:].strip()
            break

    # 3) Optional LLM stoplist stub
    custom_stop: List[str] = []
    if use_llm_stoplist:
        try:
            # Placeholder; not implemented
            raise NotImplementedError("LLM-based stoplist not implemented.")
        except NotImplementedError:
            custom_stop = []

    # 4) Extract all headings (levels 2–6) relative to topic_text
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
        default=3,
        help="Min # of headings at level ≤ max_split_level to trigger topic splitting (default: 3)."
    )
    parser.add_argument(
        "--max_split_level",
        type=int,
        default=2,
        help="Max heading level to split topics on (1=H1, 2=H2, etc., default: 2)."
    )
    parser.add_argument(
        "--tfidf_threshold",
        type=float,
        default=0.9,
        help="TF-IDF cosine threshold to merge adjacent topic chunks (default: 0.9)."
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Max tokens per final chunk (default: 1200)."
    )
    parser.add_argument(
        "--lower_threshold",
        type=int,
        default=LOWER_THRESHOLD,
        help="Min tokens to consider merging small final chunks (default: 500)."
    )
    parser.add_argument(
        "--merge_threshold",
        type=float,
        default=MERGE_THRESHOLD,
        help="Cosine similarity threshold for merging adjacent small final chunks (default: 0.3)."
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
        default=False,
        help="If set, skip writing any final chunk that is only a header."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="final_output",
        help="Directory to write final chunked .md files (default: ./final_output)."
    )
    parser.add_argument(
        "--merge_chunks",
        action="store_true",
        default=False, # Merging is off by default
        help="Enable merging of small chunk files in the deepest subdirectories."
    )
    parser.add_argument(
        "--max_merged_chunk_tokens",
        type=int,
        default=1200,
        help="Maximum token count for a merged chunk file (default: 1200)."
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

    abs_input_dir = os.path.abspath(args.input_path if os.path.isdir(args.input_path) else os.path.dirname(args.input_path))


    for md_path in md_files: # md_path from os.walk is already absolute. If single file, it's made absolute below.
        current_md_path_abs = os.path.abspath(md_path) # Ensure absolute for robustness

        relative_topic_file_path = os.path.relpath(current_md_path_abs, abs_input_dir)
        mirrored_structure_path = os.path.dirname(relative_topic_file_path)
        topic_slug_from_filename = os.path.splitext(os.path.basename(current_md_path_abs))[0]

        if mirrored_structure_path == "" or mirrored_structure_path == ".":
            final_topic_chunk_dir = os.path.join(args.output_dir, topic_slug_from_filename)
        else:
            final_topic_chunk_dir = os.path.join(args.output_dir, mirrored_structure_path, topic_slug_from_filename)

        # The following print statements for path verification can be commented out if too verbose later
        # print(f"--- Processing topic file: {current_md_path_abs} ---")
        # print(f"  Absolute input dir for relpath: {abs_input_dir}")
        # print(f"  Relative path to topic file: {relative_topic_file_path}")
        # print(f"  Mirrored structure path: {mirrored_structure_path}")
        # print(f"  Topic slug: {topic_slug_from_filename}")
        # print(f"  Target chunk output directory: {final_topic_chunk_dir}")

        try:
            print(f"Processing topic file: {current_md_path_abs} -> into {final_topic_chunk_dir}")
            os.makedirs(final_topic_chunk_dir, exist_ok=True)

            with open(current_md_path_abs, "r", encoding="utf-8") as f:
                topic_text_content = f.read()

            final_chunks_data = process_topic_text(
                topic_slug=topic_slug_from_filename,
                topic_text=topic_text_content,
                original_filename=relative_topic_file_path, # Using relative path for metadata
                mode=args.mode,
                chunk_size=args.chunk_size,
                lower_threshold=args.lower_threshold,
                merge_threshold=args.merge_threshold,
                use_llm_stoplist=args.use_llm_stoplist,
                output_dir=final_topic_chunk_dir,
                drop_empty_headers=args.drop_empty_headers
            )

            if args.mode == "md":
                num_files_written_for_topic = 0
                if os.path.exists(final_topic_chunk_dir):
                    num_files_written_for_topic = len(os.listdir(final_topic_chunk_dir))

                # print(f"  {num_files_written_for_topic} chunk files written for topic {topic_slug_from_filename} in {final_topic_chunk_dir}")
                total_written += num_files_written_for_topic
            else: # mode == "embed"
                total_written += len(final_chunks_data)
                # print(f"  {len(final_chunks_data)} embed chunks generated for topic {topic_slug_from_filename}")

        except Exception as e:
            print(f"Error processing topic file {current_md_path_abs}: {e}")
            # import traceback
            # traceback.print_exc()

    # Update final summary prints
    # Update final summary prints
    if args.mode == "md":
        print(f"\nTotal initial chunked Markdown files written: {total_written} under base directory '{args.output_dir}'.")
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

