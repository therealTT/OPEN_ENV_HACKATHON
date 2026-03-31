"""
Renders a structured observation dict for the current session state.
The observation `content` is what the agent reads.
"""
from portal.session import SessionState
from portal import database as db


def _nav(*items):
    nav_map = {
        "home":          {"id": "nav_home",          "type": "link", "label": "Home"},
        "drug_search":   {"id": "nav_drug_search",   "type": "link", "label": "Drug Approval Search"},
        "doc_archive":   {"id": "nav_doc_archive",   "type": "link", "label": "Document Archive"},
        "forms_hub":     {"id": "nav_forms_hub",     "type": "link", "label": "Submit a Form"},
    }
    return [nav_map[i] for i in items if i in nav_map]


def render(session: SessionState) -> dict:
    page = session.current_page
    if page == "home":
        return _home(session)
    if page == "drug_search":
        return _drug_search(session)
    if page == "drug_detail":
        return _drug_detail(session)
    if page == "doc_archive":
        return _doc_archive(session)
    if page == "doc_detail":
        return _doc_detail(session)
    if page == "forms_hub":
        return _forms_hub(session)
    if page == "form_labeling":
        return _form_labeling(session)
    if page == "confirmation":
        return _confirmation(session)
    if page == "error":
        return _error_page(session)
    return _home(session)


# ── Pages ─────────────────────────────────────────────────────────────────────

def _base(session: SessionState, page: str, title: str, content: str,
          elements: list, data: dict | None = None) -> dict:
    return {
        "current_page": page,
        "title": title,
        "content": content,
        "elements": elements,
        "data": data or {},
        "error": session.error_message,
        "task": session.task_description,
        "step": session.step_count,
        "steps_remaining": session.steps_remaining,
    }


def _home(session: SessionState) -> dict:
    return _base(
        session, "home",
        "Drug Regulatory Portal",
        "Welcome to the Drug Regulatory Portal. "
        "Search for approved drugs, retrieve prescribing documents, or submit regulatory forms.",
        [
            {"id": "nav_drug_search", "type": "link", "label": "Drug Approval Search"},
            {"id": "nav_doc_archive", "type": "link", "label": "Document Archive"},
            {"id": "nav_forms_hub",   "type": "link", "label": "Submit a Form"},
        ],
    )


def _drug_search(session: SessionState) -> dict:
    elements = [
        {"id": "drug_name",   "type": "input",  "label": "Drug Name (search)"},
        {"id": "app_number",  "type": "input",  "label": "Application Number (search)"},
        {"id": "search_btn",  "type": "button", "label": "Search"},
        *_nav("home"),
    ]
    data: dict = {}

    if session.drug_search_results:
        data["results"] = session.drug_search_results
        for r in session.drug_search_results:
            name = r["drug_name"]
            elements.append({
                "id":    f"result_{name}",
                "type":  "link",
                "label": f"{name} — {r['app_number']} ({r['status']})",
            })

    content = "Search for approved drugs by name or application number."
    if session.drug_search_query and not session.drug_search_results:
        content = f"No results found for '{session.drug_search_query}'."
    elif session.drug_search_results:
        content = (
            f"Found {len(session.drug_search_results)} result(s) "
            f"for '{session.drug_search_query}'. Click a drug name to view details."
        )

    return _base(session, "drug_search", "Drug Approval Search", content, elements, data)


def _drug_detail(session: SessionState) -> dict:
    drug = session.current_drug_data or {}
    return _base(
        session, "drug_detail",
        f"Drug Detail: {drug.get('drug_name', '')}",
        "Full approval record for this drug.",
        [
            *_nav("home", "drug_search"),
        ],
        data=drug,
    )


def _doc_archive(session: SessionState) -> dict:
    drug_options  = db.all_drug_names()
    type_options  = db.all_doc_types()

    elements = [
        {
            "id": "doc_drug_filter", "type": "select", "label": "Filter by Drug",
            "options": ["(all)"] + drug_options,
        },
        {
            "id": "doc_type_filter", "type": "select", "label": "Filter by Document Type",
            "options": ["(all)"] + type_options,
        },
        {"id": "search_docs_btn", "type": "button", "label": "Search Documents"},
        *_nav("home"),
    ]
    data: dict = {}

    if session.doc_search_results:
        data["results"] = session.doc_search_results
        for doc in session.doc_search_results:
            elements.append({
                "id":    f"doc_{doc['doc_id']}",
                "type":  "link",
                "label": f"{doc['doc_type']} — {doc['drug_name']} ({doc['doc_id']})",
            })

    content = "Browse and filter regulatory documents."
    if session.doc_filter_drug or session.doc_filter_type:
        filters = []
        if session.doc_filter_drug:
            filters.append(f"drug={session.doc_filter_drug}")
        if session.doc_filter_type:
            filters.append(f"type={session.doc_filter_type}")
        if session.doc_search_results:
            content = (
                f"Found {len(session.doc_search_results)} document(s) "
                f"matching {', '.join(filters)}. Click a document to view."
            )
        else:
            content = f"No documents found for {', '.join(filters)}."

    return _base(session, "doc_archive", "Document Archive", content, elements, data)


def _doc_detail(session: SessionState) -> dict:
    doc = session.current_doc_data or {}
    return _base(
        session, "doc_detail",
        f"Document: {doc.get('doc_type', '')} — {doc.get('drug_name', '')}",
        f"Document ID: {doc.get('doc_id', '')}. Review the content fields below.",
        [*_nav("home", "doc_archive")],
        data=doc,
    )


def _forms_hub(session: SessionState) -> dict:
    return _base(
        session, "forms_hub",
        "Submit a Regulatory Form",
        "Select a form type to begin.",
        [
            {"id": "nav_form_labeling", "type": "link", "label": "Labeling Inquiry"},
            {"id": "nav_form_safety",   "type": "link", "label": "Safety Report"},
            *_nav("home"),
        ],
    )


def _form_labeling(session: SessionState) -> dict:
    f = session.form_fields
    return _base(
        session, "form_labeling",
        "Labeling Inquiry Form",
        "Complete all required fields and submit.",
        [
            {"id": "drug_name",     "type": "input", "label": "Drug Name",          "value": f.get("drug_name", "")},
            {"id": "app_number",    "type": "input", "label": "Application Number",  "value": f.get("app_number", "")},
            {"id": "approval_date", "type": "input", "label": "Approval Date (YYYY-MM-DD)", "value": f.get("approval_date", "")},
            {"id": "manufacturer",  "type": "input", "label": "Manufacturer",        "value": f.get("manufacturer", "")},
            {"id": "inquiry_text",  "type": "input", "label": "Inquiry Description (optional)", "value": f.get("inquiry_text", "")},
            {"id": "submit_form",   "type": "button", "label": "Submit Form"},
            *_nav("home", "forms_hub"),
        ],
        data={"current_values": f},
    )


def _confirmation(session: SessionState) -> dict:
    return _base(
        session, "confirmation",
        "Submission Confirmed",
        f"Your form has been submitted successfully. "
        f"Reference number: {session.submission_id}",
        [*_nav("home")],
        data={
            "submission_id": session.submission_id,
            "submitted_fields": session.form_fields,
        },
    )


def _error_page(session: SessionState) -> dict:
    return _base(
        session, "error",
        "Error",
        session.error_message or "An error occurred.",
        [*_nav("home")],
    )
