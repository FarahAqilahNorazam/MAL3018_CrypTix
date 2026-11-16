import re
import hashlib

# Malaysian MyKad Format: 12 digits (YYMMDD-PB-###G or YYMMDDPB###G)
MYKAD_REGEX = re.compile(r'^\d{6}-?\d{2}-?\d{4}$')

def validate_mykad(raw_ic: str):
    """
    Validates Malaysian MyKad format.
    Accepts 12 numeric digits with or without hyphens (e.g., 990101-01-1234 or 990101011234).
    Returns (is_valid: bool, normalized_12_digits: str, error_message: str)
    """
    if not raw_ic:
        return False, "", "MyKad number is required."

    cleaned = raw_ic.strip().replace(" ", "")

    if not MYKAD_REGEX.match(cleaned):
        return False, "", "Invalid MyKad format. Expected 12 digits (e.g., 990101-01-1234 or 990101011234)."

    normalized = cleaned.replace("-", "")
    if len(normalized) != 12 or not normalized.isdigit():
        return False, "", "MyKad must contain exactly 12 numeric digits."

    # Validate Month (01-12) and Day (01-31) prefixes
    month = int(normalized[2:4])
    day = int(normalized[4:6])

    if month < 1 or month > 12:
        return False, "", f"Invalid birth month '{month:02d}' in MyKad."
    if day < 1 or day > 31:
        return False, "", f"Invalid birth day '{day:02d}' in MyKad."

    return True, normalized, ""


def hash_mykad(normalized_ic: str) -> str:
    """
    Computes irreversible SHA-256 cryptographic hash of normalized 12-digit MyKad.
    Used for identity tokenization in compliance with PDPA 2010.
    """
    return hashlib.sha256(normalized_ic.encode('utf-8')).hexdigest()


def mask_mykad(raw_or_normalized_ic: str) -> str:
    """
    Generates privacy-preserving masked MyKad string for UI presentation.
    Example: 990101-01-1234 or 990101011234 -> ******-**-1234
    Raw IC is never stored or displayed.
    """
    digits = re.sub(r'\D', '', str(raw_or_normalized_ic))
    if len(digits) >= 4:
        last4 = digits[-4:]
        return f"******-**-{last4}"
    return "******-**-****"
