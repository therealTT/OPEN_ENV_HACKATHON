"""
Task 2 — Document Retrieval
Find the recommended starting dose for NEXOLARA from its Prescribing Information.

Scoring:
  1.00 — visited correct doc (DOC-001) + starting_dose correct
  0.50 — visited correct doc + wrong field extracted (e.g. max_dose value)
  0.25 — correct value but wrong doc visited (or no doc visited)
  0.00 — incorrect value
"""
from portal.session import SessionState

TARGET_DOC_ID   = "DOC-001"
EXPECTED_DOSE   = "100mg once daily"


def grade(session: SessionState) -> tuple[float, str]:
    visited_correct_doc = (
        session.visited_doc_detail_for is not None
        and session.visited_doc_detail_for == TARGET_DOC_ID
    )

    submitted_dose = session.answer_fields.get("starting_dose", "").strip().lower()
    correct_dose   = _match(submitted_dose, EXPECTED_DOSE)

    if correct_dose and visited_correct_doc:
        return 1.0, "Correct starting dose extracted from the correct document."
    if not correct_dose and visited_correct_doc:
        return 0.5, f"Correct document visited but wrong value extracted. Got: '{submitted_dose}'."
    if correct_dose and not visited_correct_doc:
        return 0.25, "Correct value but Prescribing Information document was never opened (possible hallucination)."
    return 0.0, f"Incorrect value and/or wrong document. Got: '{submitted_dose}'."


def _match(got: str, expected: str) -> bool:
    return got == expected.strip().lower()
