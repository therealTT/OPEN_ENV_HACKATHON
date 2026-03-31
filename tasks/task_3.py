"""
Task 3 — Form Submission
Submit a Labeling Inquiry for NEXOLARA with correct app_number,
approval_date, and manufacturer.

Scoring:
  1.00 — form submitted + all 3 key fields correct
  0.75 — form submitted + 2/3 key fields correct
  0.50 — form submitted + 1/3 key fields correct
  0.25 — form reached (form_labeling page visited) but not submitted
  0.00 — form never reached
"""
from portal.session import SessionState

EXPECTED = {
    "drug_name":     "nexolara",
    "app_number":    "nda-042817",
    "approval_date": "2022-03-15",
    "manufacturer":  "helivar therapeutics",
}
KEY_FIELDS = ["app_number", "approval_date", "manufacturer"]


def grade(session: SessionState) -> tuple[float, str]:
    if not session.form_submitted:
        if session.current_form == "labeling_inquiry" or "form_labeling" in _page_history(session):
            return 0.25, "Labeling Inquiry form was opened but not submitted."
        return 0.0, "Form was never reached."

    fields = session.form_fields
    correct = sum(
        1 for f in KEY_FIELDS
        if _match(fields.get(f, ""), EXPECTED[f])
    )

    reasons = []
    for f in KEY_FIELDS:
        got = fields.get(f, "").strip()
        exp = EXPECTED[f]
        if _match(got, exp):
            reasons.append(f"{f} ✓")
        else:
            reasons.append(f"{f} ✗ (got '{got}', expected '{EXPECTED[f]}')")

    detail = ", ".join(reasons)

    if correct == 3:
        return 1.0,  f"Form submitted with all fields correct. {detail}"
    if correct == 2:
        return 0.75, f"Form submitted, 2/3 key fields correct. {detail}"
    if correct == 1:
        return 0.5,  f"Form submitted, 1/3 key fields correct. {detail}"
    return 0.25,     f"Form submitted but all key fields incorrect. {detail}"


def _match(got: str, expected: str) -> bool:
    return got.strip().lower() == expected.strip().lower()


def _page_history(session: SessionState) -> list[str]:
    # We don't track full history, but we can infer from current_form
    return [session.current_page, session.current_form or ""]
