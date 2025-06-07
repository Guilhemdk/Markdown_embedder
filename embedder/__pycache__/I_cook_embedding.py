#!/usr/bin/env python3
import argparse
import os
from typing import List, Dict, Optional

# Dependencies (install via pip):
# pip install tiktoken llama_index scikit-learn nltk

from llama_index.core.node_parser import TokenTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from Marking_splitter import (
    count_tokens,
    recursive_split_by_hierarchy_and_delimiters
)

from metadata_parser import (
    extract_description,
    parse_topic_from_filename,
    parse_version_context,
    parse_outline_date,
    extract_headings,
    get_headings_only,
    extract_keywords
)

# If you haven’t already, run: python3 -c "import nltk; nltk.download('stopwords')"

# --- Configuration defaults ---
DEFAULT_CHUNK_SIZE = 1200      # max tokens per chunk
LOWER_THRESHOLD = 500          # min tokens to trigger optional merging
MERGE_THRESHOLD = 0.3          # cosine-sim threshold for merging siblings

def generate_stoplist_via_llm(full_text: str) -> List[str]:
    """
    Placeholder for generating a stoplist via an LLM.
    """
    raise NotImplementedError("LLM-based stoplist generation is not implemented.")

# --- Main Ingestion Routine ---

def process_markdown_file(
    file_path: str,
    mode: str = "embed",      # "embed" or "md"
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    lower_threshold: int = LOWER_THRESHOLD,
    merge_threshold: float = MERGE_THRESHOLD,
    use_llm_stoplist: bool = False,
    output_dir: Optional[str] = None
) -> List[Dict]:
    """
    Read a Markdown file, chunk it, extract metadata.
    - If mode="embed": return [ {"text":..., "metadata": {...}}, ... ]
    - If mode="md": write chunk .md files into output_dir (default cwd) and return an empty list.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        all_text = f.read()

    # 1) File-level metadata
    cluster = "memory"
    topic = parse_topic_from_filename(file_path)
    version_context = parse_version_context(all_text)
    outline_date = parse_outline_date(all_text)
    root_id = f"{cluster}_{topic}"

    # 2) Root-level title (first H1)
    root_title = None
    for line in all_text.splitlines():
        if line.startswith("# "):
            root_title = line[2:].strip()
            break

    # 3) Optional LLM stoplist
    custom_stop = []
    if use_llm_stoplist:
        try:
            custom_stop = generate_stoplist_via_llm(all_text)
        except NotImplementedError as e:
            print(f"Warning: {e}. Proceeding without LLM-based stoplist.")
            custom_stop = []

    # 4) Extract all headings
    headings = extract_headings(all_text)

    # 5) Identify top-level sections by Level-2 headings
    level2 = [h for h in headings if h["level"] == 2]
    boundaries = [{"line_no": 0, "section_number": None, "heading_text": root_title}]
    boundaries += level2
    boundaries.append({"line_no": len(all_text.splitlines()), "section_number": None})

    # 6) If in "md" mode, ensure output_dir exists
    if mode == "md":
        if output_dir is None:
            output_dir = os.getcwd()
        os.makedirs(output_dir, exist_ok=True)

    chunks_out = []
    last_chunk_title = root_title

    # 7) Process each top-level section
    for i in range(len(boundaries) - 1):
        sec_start = boundaries[i]["line_no"]
        sec_end = boundaries[i+1]["line_no"]
        section_lines = all_text.splitlines()[sec_start:sec_end]
        section_text = "\n".join(section_lines)

        # 7a) Recursively split by headings and delimiters
        section_chunks = recursive_split_by_hierarchy_and_delimiters(
            section_text,
            headings,
            sec_start,
            sec_end,
            chunk_size
        )

        for chunk in section_chunks:
            text = chunk["text"]

            # 7b) Determine own_heading (first heading in chunk or inherited)
            local_headings = get_headings_only(text)
            if not local_headings:
                own_heading = last_chunk_title
            elif len(local_headings) == 1:
                own_heading = local_headings[0]
            else:
                # “Previous-title” logic
                if last_chunk_title in local_headings:
                    idx = local_headings.index(last_chunk_title)
                    if idx + 1 < len(local_headings):
                        own_heading = local_headings[idx + 1]
                    else:
                        own_heading = local_headings[idx]
                else:
                    own_heading = local_headings[0]
            last_chunk_title = own_heading

            # 7c) Extract section_number if present, else synthetic
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
            chunk_id = f"{cluster}_{topic}_sec{sec_num}"

            # 7d) Build section_hierarchy from headings before chunk start
            ancestors = [
                h["heading_text"] for h in headings
                if h["line_no"] <= chunk["start_line"]
            ]
            section_hierarchy = ancestors

            # 7e) Keywords and description
            keywords = extract_keywords(text, custom_stop)
            description = extract_description(text)

            metadata = {
                "id": chunk_id,
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

    # 8) Optional merging of tiny sibling chunks
    if mode == "embed" and lower_threshold and merge_threshold:
        merged = []
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

# --- Main Entry Point ---

def main():
    parser = argparse.ArgumentParser(
        description="Chunk a Markdown file into embedding-ready pieces and generate metadata."
    )
    parser.add_argument(
        "file_path",
        help="Path to the Markdown file to process."
    )
    parser.add_argument(
        "--mode",
        choices=["embed", "md"],
        default="embed",
        help="Mode: 'embed' returns (text, metadata) tuples; 'md' writes chunk .md files."
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Maximum token length per chunk (default: 1200)."
    )
    parser.add_argument(
        "--lower_threshold",
        type=int,
        default=LOWER_THRESHOLD,
        help="Minimum token length to consider merging small chunks (default: 500)."
    )
    parser.add_argument(
        "--merge_threshold",
        type=float,
        default=MERGE_THRESHOLD,
        help="Cosine similarity threshold for merging adjacent small chunks (default: 0.3)."
    )
    parser.add_argument(
        "--use_llm_stoplist",
        action="store_true",
        help="Flag to generate a stoplist via LLM (requires implementing generate_stoplist_via_llm)."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Directory in which to write chunked .md files (required if --mode md)."
    )

    args = parser.parse_args()

    results = process_markdown_file(
        args.file_path,
        mode=args.mode,
        chunk_size=args.chunk_size,
        lower_threshold=args.lower_threshold,
        merge_threshold=args.merge_threshold,
        use_llm_stoplist=args.use_llm_stoplist,
        output_dir=args.output_dir
    )

    if args.mode == "embed":
        # Print metadata summaries
        for idx, item in enumerate(results):
            print(f"=== Chunk {idx+1} ===")
            print(f"ID: {item['metadata']['id']}")
            print(f"Title: {item['metadata']['title']}")
            print(f"Section Hierarchy: {item['metadata']['section_hierarchy']}")
            print(f"Keywords: {item['metadata']['keywords']}")
            print(f"Description: {item['metadata']['description']}")
            print("---\n")
    else:
        print(f"Chunked Markdown files have been written to {args.output_dir or os.getcwd()}.")

if __name__ == "__main__":
    main()

