import re
from dataclasses import dataclass
from datetime import date

_EMPLOYER_SUFFIXES = {
    "ag",
    "gmbh",
    "ltd",
    "llc",
    "inc",
    "corp",
    "co",
    "se",
    "plc",
    "sa",
    "bv",
    "oy",
    "ab",
    "kg",
    "ug",
}

_TITLE_STOPWORDS = {"the", "a", "an", "and", "of", "for", "to", "in", "at", "on"}


@dataclass(frozen=True)
class PersonIdentity:
    email: str | None
    first_name: str
    last_name: str
    date_of_birth: date | None

    def key(self) -> str:
        if self.email and self.email.strip():
            return f"email:{self.email.strip().lower()}"
        first_token = _first_name_token(self.first_name)
        last = self.last_name.strip().lower()
        dob = self.date_of_birth.isoformat() if self.date_of_birth else ""
        return f"name:{first_token}|{last}|{dob}"


@dataclass(frozen=True)
class EmploymentFingerprint:
    title: str | None
    organization: str | None
    city: str | None
    start_year: int | None
    start_month: int | None
    end_year: int | None
    end_month: int | None


def _first_name_token(first_name: str) -> str:
    parts = first_name.strip().lower().split()
    return parts[0] if parts else ""


def normalize_employer(value: str | None) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", value.lower())
    tokens = [token for token in cleaned.split() if token and token not in _EMPLOYER_SUFFIXES]
    return " ".join(tokens)


def title_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    cleaned = re.sub(r"[^\w\s]", " ", value.lower())
    tokens: set[str] = set()
    for token in cleaned.split():
        if not token or token in _TITLE_STOPWORDS:
            continue
        # Strip common gendered / language suffixes (Managerin -> manager).
        stem = token
        for suffix in ("innen", "erin", "in", "er"):
            if len(stem) > len(suffix) + 2 and stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        tokens.add(stem)
    return tokens


def title_similarity(left: str | None, right: str | None) -> float:
    left_tokens = title_tokens(left)
    right_tokens = title_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = left_tokens & right_tokens
    return len(overlap) / len(left_tokens | right_tokens)


def employers_match(left: str | None, right: str | None) -> bool:
    a = normalize_employer(left)
    b = normalize_employer(right)
    if not a or not b:
        return False
    return a == b or a in b or b in a


def dates_compatible(left: EmploymentFingerprint, right: EmploymentFingerprint) -> bool:
    if left.start_year is None or right.start_year is None:
        return False
    if abs(left.start_year - right.start_year) > 1:
        return False

    left_end = left.end_year
    right_end = right.end_year
    if left_end is None and right_end is None:
        return True
    if left_end is None or right_end is None:
        return False
    return abs(left_end - right_end) <= 1


def employments_match(left: EmploymentFingerprint, right: EmploymentFingerprint) -> bool:
    """Same underlying role: shared employer and compatible dates.

    Title is intentionally soft so translated / tailored wording still matches.
    Distinct roles at the same company stay separate via non-overlapping dates.
    """
    if not employers_match(left.organization, right.organization):
        return False
    if not dates_compatible(left, right):
        return False
    return True
