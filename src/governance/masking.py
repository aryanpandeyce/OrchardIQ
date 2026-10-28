"""Post-execution Role-Based Access Control (RBAC) column masking for Restricted PII."""

import hashlib
from typing import Dict, List, Any, Optional


PII_COLUMNS = {
    "first_name",
    "last_name",
    "email",
    "phone",
    "street_address",
}


def mask_email(email: str) -> str:
    """Mask email while preserving deterministic SHA-256 token for joinability."""
    if not email or "@" not in email:
        return "***MASKED***"
    h = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:12]
    domain = email.split("@")[-1]
    return f"anon_{h}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask all but the last 4 digits of a telephone number."""
    if not phone:
        return "***-***-****"
    digits = [c for c in phone if c.isdigit()]
    if len(digits) >= 4:
        last4 = "".join(digits[-4:])
        return f"+1-***-***-{last4}"
    return "***-***-****"


def mask_name(name: str) -> str:
    """Mask name keeping only initial letter."""
    if not name:
        return "***"
    return f"{name[0]}***"


def mask_value(column_name: str, value: Any, user_role: str) -> Any:
    """Apply masking rules based on column classification and active user role."""
    if user_role == "admin":
        return value

    if value is None:
        return None

    val_str = str(value)
    col_lower = column_name.lower()

    if col_lower == "email":
        return mask_email(val_str)
    elif col_lower == "phone":
        return mask_phone(val_str)
    elif col_lower in ("first_name", "last_name"):
        return mask_name(val_str)
    elif col_lower in ("street_address", "address"):
        return "***REDACTED RESIDENTIAL ADDRESS***"

    return value


def mask_result_rows(
    rows: List[Dict[str, Any]],
    user_role: Optional[str] = None,
    role: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Mask all Restricted PII fields in query result rows for non-admin roles."""
    effective_role = role or user_role or "analyst"
    if effective_role == "admin" or not rows:
        return rows

    masked_rows = []
    for row in rows:
        new_row = {}
        for col, val in row.items():
            if col.lower() in PII_COLUMNS:
                new_row[col] = mask_value(col, val, user_role)
            else:
                new_row[col] = val
        masked_rows.append(new_row)

    return masked_rows
