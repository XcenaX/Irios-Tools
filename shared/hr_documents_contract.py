from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


PRODUCT_CODE = "hr_documents"
PRODUCT_VERSION = 1


EMPLOYMENT_CONTRACT_REQUIRED_FIELDS = [
    "employee_full_name",
    "employee_iin",
    "employee_id_doc_type",
    "employee_id_doc_number",
    "employee_id_doc_issuer",
    "employee_id_doc_issue_date",
    "employment_start_date",
    "employee_position",
    "employee_salary",
    "employer_name",
    "employer_director_name",
]

HIRE_ORDER_REQUIRED_FIELDS = [
    "hire_order_number",
    "hire_order_date",
    "employee_full_name",
    "employee_position",
    "probation_months",
    "hire_order_basis",
]

VACATION_REQUIRED_FIELDS = [
    "employee_full_name",
    "employment_start_date",
    "vacation_start_date",
    "vacation_end_date",
]


def required_fields_for_document(document_kind: str) -> list[str]:
    if document_kind == "employment_contract":
        return list(EMPLOYMENT_CONTRACT_REQUIRED_FIELDS)
    if document_kind == "hire_order":
        return list(HIRE_ORDER_REQUIRED_FIELDS)
    if document_kind == "vacation":
        return list(VACATION_REQUIRED_FIELDS)
    return []


def build_result_payload(
    *,
    organization_code: str,
    selected_template_code: str,
    selected_salary_clause_mode: str,
    employee_variables: dict[str, Any],
    organization_variables: dict[str, Any],
    manual_values: dict[str, Any],
    validation: dict[str, Any],
    job_history: list[dict[str, Any]],
    vacation_history: list[dict[str, Any]],
    document_requests: list[str],
) -> dict[str, Any]:
    return {
        "organization_code": organization_code,
        "selected_template_code": selected_template_code,
        "selected_salary_clause_mode": selected_salary_clause_mode,
        "document_requests": document_requests,
        "employee_variables": employee_variables,
        "organization_variables": organization_variables,
        "manual_values": manual_values,
        "validation": validation,
        "job_history": job_history,
        "vacation_history": vacation_history,
        "generated_at": datetime.now(UTC).isoformat(),
    }
