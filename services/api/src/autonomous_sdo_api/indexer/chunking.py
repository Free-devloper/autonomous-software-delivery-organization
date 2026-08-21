import hashlib
import re
from pathlib import Path

from autonomous_sdo_api.indexer.models import ChunkType, CodeChunk


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def chunk_code(
    file_path: str,
    content: str,
    max_lines: int = 50,
    overlap_lines: int = 10,
) -> list[CodeChunk]:
    """Split source code into overlapping line-based chunks."""
    lines = content.splitlines()
    if not lines:
        return []

    chunks: list[CodeChunk] = []
    total_lines = len(lines)
    start_idx = 0
    chunk_index = 0

    while start_idx < total_lines:
        end_idx = min(start_idx + max_lines, total_lines)
        chunk_text = "\n".join(lines[start_idx:end_idx])
        c_hash = compute_content_hash(chunk_text)
        chunk_id = f"chk_{c_hash[:12]}_{chunk_index}"

        chunks.append(
            CodeChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                start_line=start_idx + 1,
                end_line=end_idx,
                content=chunk_text,
                content_hash=c_hash,
                chunk_type=ChunkType.CODE,
            )
        )

        chunk_index += 1
        if end_idx >= total_lines:
            break
        start_idx += max_lines - overlap_lines

    return chunks


def chunk_markdown(file_path: str, content: str) -> list[CodeChunk]:
    """Split Markdown/documentation files by major section headings and paragraphs."""
    lines = content.splitlines()
    if not lines:
        return []

    chunks: list[CodeChunk] = []
    heading_pattern = re.compile(r"^#{1,3}\s+")

    current_lines: list[str] = []
    start_line = 1
    chunk_index = 0

    for idx, line in enumerate(lines, start=1):
        if heading_pattern.match(line) and current_lines:
            chunk_text = "\n".join(current_lines).strip()
            if chunk_text:
                c_hash = compute_content_hash(chunk_text)
                chunk_id = f"chk_{c_hash[:12]}_{chunk_index}"
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=idx - 1,
                        content=chunk_text,
                        content_hash=c_hash,
                        chunk_type=ChunkType.DOC,
                    )
                )
                chunk_index += 1
            current_lines = [line]
            start_line = idx
        else:
            current_lines.append(line)

    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if chunk_text:
            c_hash = compute_content_hash(chunk_text)
            chunk_id = f"chk_{c_hash[:12]}_{chunk_index}"
            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=len(lines),
                    content=chunk_text,
                    content_hash=c_hash,
                    chunk_type=ChunkType.DOC,
                )
            )

    return chunks


def chunk_file(file_path: str, content: str) -> list[CodeChunk]:
    """Dispatch to the appropriate chunking strategy based on file type."""
    ext = Path(file_path).suffix.lower()
    if ext in (".md", ".mdx", ".txt", ".rst", ".adoc"):
        return chunk_markdown(file_path, content)
    return chunk_code(file_path, content)
