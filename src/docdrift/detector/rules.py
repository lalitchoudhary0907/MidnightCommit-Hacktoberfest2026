"""Deterministic rules for detecting documentation drift."""

import re
from collections import defaultdict
from collections.abc import Iterable

from docdrift.models import CodeFact, DocumentationClaim, DriftFinding


INLINE_CODE = re.compile(r"`+([^`\n]+?)`+")
SYMBOL_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*"
    r"(?:\(\))?"
    r"(?![A-Za-z0-9_])"
)

CAMEL_CASE = re.compile(
    r"^[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]+)+$"
)


def _is_explicit_symbol(token: str) -> bool:
    """Return True only for identifiers that look like code symbols."""

    token = token.strip()

    if token.endswith("()"):
        token = token[:-2]

    if not token or not re.fullmatch(
        r"(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*",
        token,
    ):
        return False

    return (
        "." in token
        or "_" in token
        or bool(CAMEL_CASE.fullmatch(token))
    )


def _extract_symbols(claim: DocumentationClaim) -> list[str]:
    """Extract explicit code-like references from a documentation claim."""

    symbols = []

    def add(token: str) -> None:
        token = token.strip()

        if token.endswith("()"):
            token = token[:-2]

        if _is_explicit_symbol(token) and token not in symbols:
            symbols.append(token)

    for match in INLINE_CODE.finditer(claim.text):
        for token_match in SYMBOL_TOKEN.finditer(match.group(1)):
            add(token_match.group(0))

    prose = INLINE_CODE.sub(" ", claim.text)

    for match in SYMBOL_TOKEN.finditer(prose):
        add(match.group(0))

    return symbols


def _build_fact_index(
    facts: Iterable[CodeFact],
) -> dict[str, list[CodeFact]]:
    """Index code facts by their short and qualified names."""

    index = defaultdict(list)

    for fact in facts:
        aliases = {fact.name}

        qualified_name = fact.metadata.get("qualified_name")

        if isinstance(qualified_name, str) and qualified_name:
            aliases.add(qualified_name)

        if fact.owner:
            aliases.add(f"{fact.owner}.{fact.name}")

        for alias in aliases:
            if fact not in index[alias]:
                index[alias].append(fact)

    return dict(index)


def _matching_facts(
    symbol: str,
    index: dict[str, list[CodeFact]],
) -> list[CodeFact]:
    """Resolve an explicit symbol, using a unique short-name fallback."""

    normalized = symbol[:-2] if symbol.endswith("()") else symbol

    exact = index.get(normalized)

    if exact:
        return exact

    if "." in normalized:
        return index.get(normalized.rsplit(".", 1)[-1], [])

    return []


def _make_missing_symbol_finding(
    claim: DocumentationClaim,
    symbol: str,
) -> DriftFinding:
    return DriftFinding(
        rule_id="missing-symbol",
        severity="warning",
        confidence=0.85,
        title="Documented code symbol not found",
        message=(
            f"Documentation references '{symbol}', "
            "but no matching Python code definition was found."
        ),
        documentation_location=claim.location,
        documentation_text=claim.text,
        code_location=None,
        old_value=symbol,
        new_value=None,
        evidence=[
            f"Unresolved documentation reference: {symbol}",
            "The supplied Python code facts contain no matching definition.",
        ],
        related_symbol=symbol,
        recommendation=(
            "Check whether the symbol was renamed, removed, "
            "or documented with an incorrect name."
        ),
    )


def _make_ambiguous_symbol_finding(
    claim: DocumentationClaim,
    symbol: str,
    candidates: list[CodeFact],
) -> DriftFinding:
    locations = [
        f"{fact.location.path}:{fact.location.line}"
        for fact in candidates
    ]

    return DriftFinding(
        rule_id="ambiguous-symbol",
        severity="info",
        confidence=0.65,
        title="Documentation reference is ambiguous",
        message=(
            f"Documentation reference '{symbol}' matches "
            f"{len(candidates)} Python definitions."
        ),
        documentation_location=claim.location,
        documentation_text=claim.text,
        code_location=None,
        old_value=symbol,
        new_value=locations,
        evidence=[
            f"Candidate definition: {location}"
            for location in locations
        ],
        related_symbol=symbol,
        recommendation=(
            "Use a qualified module or class reference "
            "to identify the intended definition."
        ),
    )


def _make_numeric_mismatch_finding(
    claim: DocumentationClaim,
    fact: CodeFact,
    documented_value: float,
) -> DriftFinding:
    actual_value = fact.value

    return DriftFinding(
        rule_id="numeric-value-mismatch",
        severity="warning",
        confidence=0.95,
        title="Documented numeric value differs from code",
        message=(
            f"Documentation describes '{fact.name}' as "
            f"{documented_value:g}, but Python code defines "
            f"{actual_value!r}."
        ),
        documentation_location=claim.location,
        documentation_text=claim.text,
        code_location=fact.location,
        old_value=documented_value,
        new_value=actual_value,
        evidence=[
            f"Documented value: {documented_value:g}",
            f"Python value: {actual_value!r}",
            f"Matched code symbol: {fact.name}",
        ],
        related_symbol=fact.metadata.get(
            "qualified_name",
            fact.name,
        ),
        recommendation=(
            "Update the documentation or verify that the "
            "Python constant has the intended value."
        ),
    )


def detect_drift(
    claims: Iterable[DocumentationClaim],
    facts: Iterable[CodeFact],
) -> list[DriftFinding]:
    """
    Detect deterministic mismatches between Markdown claims and Python facts.

    Rules:
        - missing-symbol: an explicit code-like reference has no definition.
        - ambiguous-symbol: a reference matches multiple definitions.
        - numeric-value-mismatch: a documented numeric value differs from
          a uniquely matched Python constant or class attribute.

    A missing code definition has no code location, so its code_location
    is None rather than an invented source position.
    """

    claims = list(claims)
    facts = list(facts)

    if not all(isinstance(item, DocumentationClaim) for item in claims):
        raise TypeError("claims must contain DocumentationClaim objects.")

    if not all(isinstance(item, CodeFact) for item in facts):
        raise TypeError("facts must contain CodeFact objects.")

    index = _build_fact_index(facts)
    findings = []

    for claim in claims:
        symbols = _extract_symbols(claim)
        matched_facts = []

        for symbol in symbols:
            candidates = _matching_facts(symbol, index)

            if not candidates:
                findings.append(
                    _make_missing_symbol_finding(claim, symbol)
                )
                continue

            if len(candidates) > 1:
                findings.append(
                    _make_ambiguous_symbol_finding(
                        claim,
                        symbol,
                        candidates,
                    )
                )
                continue

            fact = candidates[0]

            if fact not in matched_facts:
                matched_facts.append(fact)

        # Compare numbers only when the association is unambiguous.
        if len(symbols) != 1 or len(matched_facts) != 1:
            continue

        fact = matched_facts[0]

        if fact.kind not in {"constant", "attribute"}:
            continue

        if isinstance(fact.value, bool) or not isinstance(
            fact.value,
            (int, float),
        ):
            continue

        documented_numbers = {
            float(number)
            for number in claim.numbers
        }

        if len(documented_numbers) != 1:
            continue

        documented_value = next(iter(documented_numbers))

        if documented_value != float(fact.value):
            findings.append(
                _make_numeric_mismatch_finding(
                    claim,
                    fact,
                    documented_value,
                )
            )

    return findings


__all__ = ["detect_drift"]
