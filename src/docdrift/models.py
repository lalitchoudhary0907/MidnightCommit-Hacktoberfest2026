from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Location:
    path: str
    line: int
    end_line: int


@dataclass(frozen=True)
class ChangedFile:
    status: str  # 'added', 'modified', 'deleted', 'renamed'
    old_path: Optional[str]
    new_path: Optional[str]


@dataclass(frozen=True)
class CodeFact:
    fact_id: str
    kind: str
    name: str
    value: Any
    owner: str
    location: Location
    language: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CodeChange:
    fact_id: str
    kind: str
    name: str
    old_value: Any
    new_value: Any
    old_location: Optional[Location]
    new_location: Optional[Location]
    owner: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentationClaim:
    claim_id: str
    text: str
    location: Location
    identifiers: List[str] = field(default_factory=list)
    numbers: List[float] = field(default_factory=list)
    section: str = ""
    block_kind: str = "text"


@dataclass(frozen=True)
class MappingResult:
    claim: DocumentationClaim
    related_changes: List[CodeChange] = field(default_factory=list)
    score: float = 0.0
    reasons: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DriftFinding:
    rule_id: str
    severity: str
    confidence: float
    title: str
    message: str
    documentation_location: Location
    documentation_text: str
    code_location: Optional[Location]
    old_value: Any
    new_value: Any
    evidence: List[str] = field(default_factory=list)
    related_symbol: str = ""
    recommendation: str = ""


@dataclass
class ScanReport:
    repository: str
    base_commit: str
    head_commit: str
    changed_files: List[ChangedFile] = field(default_factory=list)
    scanned_documents: List[str] = field(default_factory=list)
    findings: List[DriftFinding] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)