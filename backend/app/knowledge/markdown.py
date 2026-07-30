import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
TAG_PATTERN = re.compile(r"(?<!\w)#([\w\-\/]+)")
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def slugify(value: str) -> str:
    text = re.sub(r"[^\w\s\-]", "", value.lower(), flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text or f"note-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"


def note_title(path: Path, content: str) -> str:
    frontmatter, body = parse_frontmatter(content)
    if isinstance(frontmatter.get("title"), str) and frontmatter["title"].strip():
        return frontmatter["title"].strip()
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def note_category(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    return relative.parts[0] if len(relative.parts) > 1 else "Inbox"


def extract_links(content: str) -> list[str]:
    return sorted(set(match.strip() for match in LINK_PATTERN.findall(content)))


def extract_tags(content: str) -> list[str]:
    frontmatter, body = parse_frontmatter(content)
    tags = set(match.strip() for match in TAG_PATTERN.findall(body))
    raw_tags = frontmatter.get("tags", [])
    if isinstance(raw_tags, str):
        tags.update(tag.strip().lstrip("#") for tag in raw_tags.split(",") if tag.strip())
    elif isinstance(raw_tags, list):
        tags.update(str(tag).strip().lstrip("#") for tag in raw_tags if str(tag).strip())
    return sorted(tags)


def excerpt(content: str, length: int = 220) -> str:
    _, body = parse_frontmatter(content)
    compact = " ".join(line.strip("# ").strip() for line in body.splitlines() if line.strip())
    return compact[: length - 3] + "..." if len(compact) > length else compact


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content

    frontmatter: dict[str, Any] = {}
    for raw_line in match.group(1).splitlines():
        if ":" not in raw_line:
            continue
        key, raw_value = raw_line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if value.startswith("[") and value.endswith("]"):
            frontmatter[key] = [item.strip().strip('"').strip("'") for item in value[1:-1].split(",") if item.strip()]
        else:
            frontmatter[key] = value.strip('"').strip("'")
    return frontmatter, content[match.end():]


def markdown_document(title: str, content: str, tags: list[str]) -> str:
    tag_line = " ".join(f"#{tag}" for tag in tags)
    body = content.strip()
    if not body.startswith("# "):
        body = f"# {title}\n\n{body}"
    if tag_line and tag_line not in body:
        body = f"{body}\n\n{tag_line}"
    return body + "\n"
