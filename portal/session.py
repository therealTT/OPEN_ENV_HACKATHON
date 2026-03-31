from dataclasses import dataclass, field
from typing import Optional


TASK_CONFIG = {
    "task_1": {
        "description": (
            "Find the approval date and approved indication for NEXOLARA. "
            "When you have both values, submit your answer using action type 'answer' "
            "with fields: {\"approval_date\": \"...\", \"indication\": \"...\"}."
        ),
        "max_steps": 10,
    },
    "task_2": {
        "description": (
            "Find the recommended starting dose for NEXOLARA from its "
            "Prescribing Information document. "
            "When you have the value, submit your answer using action type 'answer' "
            "with fields: {\"starting_dose\": \"...\"}."
        ),
        "max_steps": 15,
    },
    "task_3": {
        "description": (
            "Submit a Labeling Inquiry form for NEXOLARA. "
            "The form requires: drug_name, app_number, approval_date, and manufacturer. "
            "You must look these up in the portal before filling the form. "
            "Navigate to: Forms Hub → Labeling Inquiry."
        ),
        "max_steps": 20,
    },
}


@dataclass
class SessionState:
    session_id: str
    task_id: str
    current_page: str = "home"
    step_count: int = 0
    done: bool = False
    error_message: Optional[str] = None

    # Drug search
    drug_search_query: str = ""
    drug_search_results: list = field(default_factory=list)
    current_drug_data: Optional[dict] = None   # set when on drug_detail

    # Doc archive
    doc_filter_drug: str = ""
    doc_filter_type: str = ""
    doc_search_results: list = field(default_factory=list)
    current_doc_data: Optional[dict] = None    # set when on doc_detail

    # Form
    current_form: Optional[str] = None         # "labeling_inquiry" | "safety_report"
    form_fields: dict = field(default_factory=dict)
    form_submitted: bool = False
    submission_id: Optional[str] = None

    # Answer (tasks 1, 2)
    answer_fields: dict = field(default_factory=dict)
    answer_submitted: bool = False

    # Grading helpers
    visited_drug_detail_for: Optional[str] = None  # drug_name
    visited_doc_detail_for: Optional[str] = None   # doc_id

    @property
    def max_steps(self) -> int:
        return TASK_CONFIG[self.task_id]["max_steps"]

    @property
    def task_description(self) -> str:
        return TASK_CONFIG[self.task_id]["description"]

    @property
    def steps_remaining(self) -> int:
        return max(0, self.max_steps - self.step_count)
