"""Markdown documentation analysis for DocDrift."""

import hashlib
import re
from pathlib import Path

from docdrift.errors import DocumentationAnalysisError
from docdrift.models import DocumentationClaim, Location


HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)\s*#*\s*$")
SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
LIST = re.compile(r"^ {0,3}(?:[-+*]|\d+[.)])[ \t]+(.*)$")
QUOTE = re.compile(r"^ {0,3}>[ \t]?(.*)$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
RULE = re.compile(r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$")

INLINE_CODE = re.compile(r"`+([^`\n]+?)`+")
IDENTIFIER = re.compile(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\b")
SNAKE = re.compile(r"\b[A-Za-z_]\w*_[A-Za-z0-9_]*\b")
CAMEL = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]+)+\b")
FUNCTION = re.compile(r"\b([A-Za-z_]\w*)[ \t]*(?=\()")
NUMBER = re.compile(
    r"(?<![A-Za-z0-9_])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    r"(?![A-Za-z0-9_])"
)


def _heading_at(lines, index):
    match = HEADING.match(lines[index])
    if match:
        return len(match.group(1)), match.group(2).strip(), index

    if index + 1 < len(lines):
        match = SETEXT.match(lines[index + 1])
        if match and lines[index].strip():
            level = 1 if match.group(1).startswith("=") else 2
            return level, lines[index].strip(), index + 1

    return None


def _identifiers(text):
    found = []

    def add(pattern, value):
        for match in pattern.finditer(value):
            item = match.group(1) if match.lastindex else match.group(0)
            if item not in found:
                found.append(item)

    for match in INLINE_CODE.finditer(text):
        add(IDENTIFIER, match.group(1))

    prose = INLINE_CODE.sub(" ", text)

    for pattern in (IDENTIFIER, SNAKE, CAMEL, FUNCTION):
        add(pattern, prose)

    return found


def _numbers(text):
    return [float(match.group(0)) for match in NUMBER.finditer(text)]


def _make_claim(path, text, start, end, section, kind):
    identity = f"{path}\0{start}\0{kind}\0{text}"
    claim_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]

    return DocumentationClaim(
        claim_id=f"md-{claim_id}",
        text=text,
        location=Location(path, start, end),
        identifiers=_identifiers(text),
        numbers=_numbers(text),
        section=section,
        block_kind=kind,
    )


def analyze_markdown_text(text: str, path: str = "<memory>"):
    """Extract headings, paragraphs, list items and blockquotes from Markdown."""
    if not isinstance(text, str):
        raise DocumentationAnalysisError("Markdown content must be a string.")

    lines = text.splitlines()
    claims = []
    heading_stack = []

    def section():
        return " > ".join(title for _, title in heading_stack)

    def emit(parts, start, end, kind):
        content = " ".join(part.strip() for part in parts if part.strip())
        if content:
            claims.append(
                _make_claim(
                    str(path), content, start + 1, end + 1, section(), kind
                )
            )

    def is_block_start(index):
        line = lines[index]
        return bool(
            FENCE.match(line)
            or _heading_at(lines, index)
            or LIST.match(line)
            or QUOTE.match(line)
            or RULE.match(line)
        )

    i = 0

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)
            closing = re.compile(
                rf"^ {{0,3}}{re.escape(marker[0])}{{{len(marker)},}}[ \t]*$"
            )
            i += 1
            while i < len(lines):
                if closing.match(lines[i]):
                    i += 1
                    break
                i += 1
            continue

        heading = _heading_at(lines, i)
        if heading:
            level, title, end = heading

            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()

            heading_stack.append((level, title))
            emit([title], i, end, "heading")
            i = end + 1
            continue

        if RULE.match(line):
            i += 1
            continue

        quote = QUOTE.match(line)
        if quote:
            start = i
            parts = []

            while i < len(lines):
                match = QUOTE.match(lines[i])
                if not match:
                    break
                parts.append(match.group(1))
                i += 1

            emit(parts, start, i - 1, "blockquote")
            continue

        item = LIST.match(line)
        if item:
            start = i
            parts = [item.group(1)]
            end = i
            i += 1

            while i < len(lines) and lines[i].strip():
                if is_block_start(i):
                    break
                if re.match(r"^(?: {2,}|\t)", lines[i]):
                    parts.append(lines[i].strip())
                    end = i
                    i += 1
                else:
                    break

            emit(parts, start, end, "list_item")
            continue

        start = i
        parts = []

        while i < len(lines) and lines[i].strip():
            if i > start and is_block_start(i):
                break
            parts.append(lines[i])
            i += 1

        emit(parts, start, i - 1, "text")

    return claims


def analyze_markdown_file(path: str | Path):
    """Read and analyze a Markdown file."""
    file_path = Path(path)

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DocumentationAnalysisError(
            f"Unable to read Markdown file '{file_path}': {exc}"
        ) from exc

    return analyze_markdown_text(content, str(file_path))


__all__ = ["analyze_markdown_text", "analyze_markdown_file"]
