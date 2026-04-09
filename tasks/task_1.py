"""
Task 1 — Drug Lookup
Find the approval date and approved indication for NEXOLARA.

Scoring:
  1 — visited drug_detail for NEXOLARA + both fields correct
  0.50 — visited drug_detail + 1 field correct
  0.25 — both fields correct but never visited drug_detail (hallucinated)
  0 — 0 fields correct
"""
from portal.session import SessionState

EXPECTED = {
    "approval_date": "2022-03-15",
    "indication":    "myelofibrosis",
}


def grade(session: SessionState) -> tuple[float, str]:
    visited = (
        session.visited_drug_detail_for is not None
        and session.visited_drug_detail_for.upper() == "NEXOLARA"
    )

    answers = session.answer_fields
    correct = 0

    if _match(answers.get("approval_date", ""), EXPECTED["approval_date"]):
        correct += 1
    if _match(answers.get("indication", ""), EXPECTED["indication"]):
        correct += 1

    if correct == 2 and visited:
        return 1, "Both fields correct and drug detail page visited."
    if correct == 1 and visited:
        return 0.5, "One field correct and drug detail page visited."
    if correct == 2 and not visited:
        return 0.25, "Both fields correct but drug detail page was never visited (possible hallucination)."
    if correct == 1 and not visited:
        return 0.1, "One field correct but drug detail page was never visited."
    return 0, f"No correct fields. Submitted: {answers}"


def _match(got: str, expected: str) -> bool:
    return got.strip().lower() == expected.strip().lower()
