#!/usr/bin/env python3
import argparse
import os
import re
import sys
from typing import List, Dict

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
    if args.mode == "md":
        print(f"\nTotal chunked Markdown files written: {total_written} under base directory '{args.output_dir}'.")
    else:
        print(f"\nTotal embedded chunks generated: {total_written} from {len(md_files)} topic files.")


if __name__ == "__main__":
    unified_main()

