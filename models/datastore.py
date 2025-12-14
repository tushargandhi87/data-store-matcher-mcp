
from dataclasses import dataclass
from typing import Optional

@dataclass
class NormalizedDatastore:
    original: str
    product: str
    version: str
    missing_version: bool

@dataclass
class MatchResult:
    original: str
    matched_name: str
    confidence: float
    reasoning: str
    match_type: str  # "exact" or "llm"
    product: Optional[str] = None
    version: Optional[str] = None

@dataclass
class APISuccessResult:
    original: str
    product: str
    version: str
    eol_cycle: str
    release_date: str
    eol_date: str
    lts: bool
    support: str  # e.g. "Supported", "EOL"
    latest_version: str
    link: str
    api_response: dict

@dataclass
class APINotFoundResult:
    original: str
    product: str
    version: str
    status: str # "not_found"
    reason: str
    api_response: dict
    attempts: int

@dataclass
class APIErrorResult:
    original: str
    product: str
    version: str
    status: str # "error"
    error_message: str
    api_response: Optional[dict]
    attempts: int

@dataclass
class DatastoreInput:
    """Represents a raw input row from the user file"""
    raw_name_string: str
    # Add other fields if user input has more columns, but for now assuming just the name is key
