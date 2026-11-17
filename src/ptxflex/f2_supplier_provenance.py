"""Independent documentary provenance screen; not vessel certification or LCA."""
import re
from datetime import date
from urllib.parse import urlsplit

def check_supplier_provenance(row):
    """Fail closed: documentary identifiers are necessary, never sufficient."""
    errors = []
    if not isinstance(row, dict):
        return ["supplier evidence must be a mapping"]
    url = row.get("supplier_source_url")
    try:
        p = urlsplit(url) if isinstance(url, str) else None
        if not p or p.scheme != "https" or not p.hostname or p.username or p.password:
            raise ValueError("invalid HTTPS supplier URL")
        if p.hostname.lower() in ("example.com", "example.org", "example.net", "localhost"):
            raise ValueError("placeholder supplier URL")
    except ValueError:
        errors.append("invalid or placeholder supplier URL")
    digest = row.get("supplier_document_sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        errors.append("missing or invalid document SHA-256")
    for field in ("supplier_document_receipt_id", "independent_reviewer_id"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            errors.append("missing " + field)
    for field in ("source_date", "independent_review_date"):
        try:
            value = row[field]
            if not isinstance(value, str) or date.fromisoformat(value) > date.today():
                raise ValueError("invalid or future date")
        except (KeyError, TypeError, ValueError):
            errors.append("missing, invalid or future " + field)
    if row.get("independent_review") is not True:
        errors.append("independent review not confirmed")
    return errors

def audit_provenance_for_all(records, required_categories):
    """A valid-looking receipt cannot establish that an archive exists."""
    return {name: check_supplier_provenance(records.get(name))
            for name in sorted(required_categories)
            if check_supplier_provenance(records.get(name))}
