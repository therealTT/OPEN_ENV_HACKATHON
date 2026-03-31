"""
Handles agent actions and mutates session state accordingly.
Returns (updated_session, error_message_or_None).
"""
from portal.session import SessionState
from portal import database as db


def handle(session: SessionState, action: dict) -> tuple[SessionState, str | None]:
    session.error_message = None
    action_type = action.get("type", "")

    if action_type == "navigate":
        return _navigate(session, action)
    if action_type == "fill":
        return _fill(session, action)
    if action_type == "select":
        return _select(session, action)
    if action_type == "click":
        return _click(session, action)
    if action_type == "submit":
        return _submit(session, action)
    if action_type == "answer":
        return _answer(session, action)

    session.error_message = f"Unknown action type '{action_type}'. Valid types: navigate, fill, select, click, submit, answer."
    session.current_page = "error"
    return session, session.error_message


# ── Action handlers ────────────────────────────────────────────────────────────

def _navigate(session: SessionState, action: dict):
    page = action.get("page", "")
    allowed = {"home", "drug_search", "doc_archive", "forms_hub"}
    if page in allowed:
        session.current_page = page
        return session, None
    if page not in allowed:
        session.error_message = (
            f"Cannot navigate directly to '{page}'. "
            f"Allowed top-level pages: {sorted(allowed)}. "
            "Detail pages are reached by clicking on search results."
        )
        session.current_page = "error"
        return session, session.error_message
    return session, None


def _fill(session: SessionState, action: dict):
    eid   = action.get("element_id", "")
    value = action.get("value", "")

    # Drug search inputs
    if eid == "drug_name" and session.current_page == "drug_search":
        session.drug_search_query = value
        return session, None

    if eid == "app_number" and session.current_page == "drug_search":
        session.drug_search_query = value
        return session, None

    # Doc archive filters (also accepts select)
    if eid == "doc_drug_filter":
        session.doc_filter_drug = "" if value == "(all)" else value
        return session, None

    if eid == "doc_type_filter":
        session.doc_filter_type = "" if value == "(all)" else value
        return session, None

    # Form labeling fields
    form_fields = {"drug_name", "app_number", "approval_date", "manufacturer", "inquiry_text"}
    if eid in form_fields and session.current_page == "form_labeling":
        session.form_fields[eid] = value
        return session, None

    session.error_message = f"Element '{eid}' not found on page '{session.current_page}'."
    return session, session.error_message


def _select(session: SessionState, action: dict):
    # Treat select the same as fill
    return _fill(session, action)


def _click(session: SessionState, action: dict):
    eid = action.get("element_id", "")

    # ── Navigation links ──────────────────────────────────────────────────────
    nav_map = {
        "nav_home":          "home",
        "nav_drug_search":   "drug_search",
        "nav_doc_archive":   "doc_archive",
        "nav_forms_hub":     "forms_hub",
        "nav_form_labeling": "form_labeling",
        "nav_form_safety":   "error",        # not implemented; graceful error
    }
    if eid in nav_map:
        target = nav_map[eid]
        if target == "error":
            session.error_message = "Safety Report form is not available in this environment."
            session.current_page = "error"
        else:
            session.current_page = target
            if target == "form_labeling":
                session.current_form = "labeling_inquiry"
        return session, None

    # ── Drug search button ────────────────────────────────────────────────────
    if eid == "search_btn":
        if not session.drug_search_query:
            session.error_message = "Please fill in a drug name or application number before searching."
            return session, session.error_message
        session.drug_search_results = db.search_drugs(session.drug_search_query)
        return session, None

    # ── Drug result links  (result_<DRUGNAME>) ────────────────────────────────
    if eid.startswith("result_"):
        drug_name = eid[len("result_"):]
        drug = db.get_drug(drug_name)
        if not drug:
            session.error_message = f"Drug '{drug_name}' not found."
            session.current_page = "error"
            return session, session.error_message
        session.current_drug_data = drug
        session.current_page = "drug_detail"
        session.visited_drug_detail_for = drug_name
        return session, None

    # ── Document search button ────────────────────────────────────────────────
    if eid == "search_docs_btn":
        session.doc_search_results = db.search_documents(
            drug_name=session.doc_filter_drug,
            doc_type=session.doc_filter_type,
        )
        return session, None

    # ── Document result links  (doc_<DOCID>) ──────────────────────────────────
    if eid.startswith("doc_"):
        doc_id = eid[len("doc_"):]
        doc = db.get_document(doc_id)
        if not doc:
            session.error_message = f"Document '{doc_id}' not found."
            session.current_page = "error"
            return session, session.error_message
        session.current_doc_data = doc
        session.current_page = "doc_detail"
        session.visited_doc_detail_for = doc_id
        return session, None

    # ── Form submit button (handled via click too) ────────────────────────────
    if eid == "submit_form":
        return _submit(session, {"form_id": "labeling_inquiry"})

    session.error_message = f"Element '{eid}' not found on page '{session.current_page}'."
    return session, session.error_message


def _submit(session: SessionState, action: dict):
    form_id = action.get("form_id", session.current_form or "")

    # Accept both the page name and the internal form id
    if form_id == "form_labeling":
        form_id = "labeling_inquiry"

    if form_id != "labeling_inquiry":
        session.error_message = f"Unknown form '{form_id}'. Use form_id 'labeling_inquiry' or navigate to the form page first."
        session.current_page = "error"
        return session, session.error_message

    required = ["drug_name", "app_number", "approval_date", "manufacturer"]
    missing  = [f for f in required if not session.form_fields.get(f, "").strip()]
    if missing:
        session.error_message = f"Required fields missing: {missing}. Please fill them before submitting."
        return session, session.error_message

    submission_id = db.submit_form("labeling_inquiry", session.form_fields)
    session.submission_id = submission_id
    session.form_submitted = True
    session.done = True
    session.current_page = "confirmation"
    return session, None


def _answer(session: SessionState, action: dict):
    # Accept nested {"fields": {...}} or flat keys directly in the action
    fields = action.get("fields", {})
    if not isinstance(fields, dict) or not fields:
        # Fall back: extract all keys except "type" as the answer fields
        fields = {k: v for k, v in action.items() if k != "type"}

    if not fields:
        session.error_message = "Answer action requires answer fields (e.g. {'type': 'answer', 'fields': {'approval_date': '...'}})."
        return session, session.error_message

    session.answer_fields = fields
    session.answer_submitted = True
    session.done = True
    return session, None
