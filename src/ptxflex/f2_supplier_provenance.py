"""Independent documentary provenance screen; not vessel certification or LCA."""
import re
import ipaddress
from collections.abc import Mapping
from datetime import date
from urllib.parse import urlsplit

def check_supplier_provenance(row):
    """Fail closed: documentary identifiers are necessary, never sufficient."""
    errors = []
    if not isinstance(row, Mapping):
        return ["supplier evidence must be a mapping"]
    url = row.get("supplier_source_url")
    try:
        p = urlsplit(url) if isinstance(url, str) else None
        if not p or p.scheme != "https" or not p.hostname or p.username or p.password:
            raise ValueError("invalid HTTPS supplier URL")
        host = p.hostname.rstrip(".").lower()
        if (host in ("example.com", "example.org", "example.net", "localhost")
                or host.endswith((".example", ".test", ".invalid", ".localhost", ".local"))
                or any(host.endswith("." + x) for x in ("example.com", "example.org", "example.net"))
                or "." not in host):
            raise ValueError("placeholder or local supplier URL")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError("IP-literal supplier URL is not admitted")
        if p.fragment or any(ch.isspace() for ch in url):
            raise ValueError("ambiguous supplier URL")
    except ValueError:
        errors.append("invalid or placeholder supplier URL")
    digest = row.get("supplier_document_sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        errors.append("missing or invalid document SHA-256")
    for field in ("supplier_document_receipt_id", "independent_reviewer_id"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            errors.append("missing " + field)
    parsed_dates = {}
    for field in ("source_date", "independent_review_date"):
        try:
            value = row[field]
            if not isinstance(value, str):
                raise ValueError("invalid date type")
            parsed = date.fromisoformat(value)
            if parsed > date.today():
                raise ValueError("future date")
            parsed_dates[field] = parsed
        except (KeyError, TypeError, ValueError):
            errors.append("missing, invalid or future " + field)
    if (len(parsed_dates) == 2 and
            parsed_dates["independent_review_date"] < parsed_dates["source_date"]):
        errors.append("independent review predates source document")
    if row.get("independent_review") is not True:
        errors.append("independent review not confirmed")
    return errors

def audit_provenance_for_all(records, required_categories):
    """A valid-looking receipt cannot establish that an archive exists."""
    return {name: check_supplier_provenance(records.get(name))
            for name in sorted(required_categories)
            if check_supplier_provenance(records.get(name))}
