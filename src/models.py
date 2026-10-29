"""
Data models representing the 12 core payroll entities.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

@dataclass
class PayGroupModel:
    pay_group_id: str
    name: str
    frequency: str
    standard_hours: float = 160.0
    max_overtime_hours: float = 40.0
    is_active: bool = True

@dataclass
class PayPeriodModel:
    pay_period_id: str
    pay_group_id: str
    start_date: str # YYYY-MM-DD
    end_date: str   # YYYY-MM-DD
    cut_off_date: str # YYYY-MM-DD
    status: str = "OPEN" # OPEN, PROCESSING, CLOSED

@dataclass
class EmployeeModel:
    employee_id: str
    pay_group_id: str
    first_name: str
    last_name: str
    email: str
    hourly_rate: float
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    tax_identifier: Optional[str] = None
    status: str = "ACTIVE" # ACTIVE, ON_LEAVE, TERMINATED
    created_at: str = ""

@dataclass
class TimeEntryModel:
    time_entry_id: str
    employee_id: str
    pay_period_id: str
    work_date: str
    regular_hours: float = 8.0
    overtime_hours: float = 0.0
    status: str = "APPROVED" # SUBMITTED, APPROVED, REJECTED
    version: int = 1
    created_at: str = ""

@dataclass
class LeaveRecordModel:
    leave_record_id: str
    employee_id: str
    pay_period_id: str
    leave_date: str
    leave_type: str # PAID_CASUAL, PAID_SICK, UNPAID_LOP
    hours_deducted: float = 8.0
    status: str = "APPROVED" # APPROVED, PENDING, REJECTED

@dataclass
class AllowanceModel:
    allowance_id: str
    employee_id: str
    pay_period_id: str
    allowance_type: str # HOUSING, CONVEYANCE, MEAL_STIPEND, SHIFT_ALLOWANCE
    amount: float
    is_taxable: bool = True

@dataclass
class DeductionModel:
    deduction_id: str
    employee_id: str
    pay_period_id: str
    deduction_type: str # PROVIDENT_FUND, PROFESSIONAL_TAX, UNPAID_LEAVE, HEALTH_INSURANCE
    amount: float
    source_ref_id: Optional[str] = None

@dataclass
class PayrollInputModel:
    payroll_input_id: str
    employee_id: str
    pay_period_id: str
    regular_hours: float = 0.0
    overtime_hours: float = 0.0
    base_earnings: float = 0.0
    overtime_earnings: float = 0.0
    total_allowance: float = 0.0
    total_deduction: float = 0.0
    gross_pay: float = 0.0
    net_pay: float = 0.0
    reconciliation_variance: float = 0.0
    status: str = "DRAFT" # DRAFT, VALIDATED, FLAGGED, APPROVED, EXPORTED
    aggregated_at: str = ""

@dataclass
class ValidationRuleModel:
    rule_id: str
    rule_name: str
    category: str
    severity: str
    description: str

@dataclass
class ExceptionModel:
    exception_id: str
    rule_id: str
    entity_type: str
    entity_id: str
    employee_id: str
    pay_period_id: str
    issue_type: str
    status: str = "OPEN" # OPEN, RESOLVED, OVERRIDDEN
    details: str = "{}"
    created_at: str = ""

@dataclass
class ApprovalModel:
    approval_id: str
    payroll_input_id: str
    approver_role: str # MANAGER, HR_PARTNER, FINANCE_CONTROLLER
    approver_id: str
    decision: str # APPROVED, REJECTED, REVISION_REQUESTED
    comments: str = ""
    decided_at: str = ""

@dataclass
class PayrollExportModel:
    export_id: str
    payroll_input_id: str
    pay_period_id: str
    employee_id: str
    bank_account_no: str
    approved_gross: float
    approved_net: float
    reconciliation_hash: str
    export_timestamp: str = ""
