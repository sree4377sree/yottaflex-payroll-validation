"""
Validation Rules & Reconciliation Engine.
Executes business rules, records traceable exceptions, and updates lifecycle states.
"""

from typing import List, Dict, Tuple, Any
from datetime import datetime, timezone

from src.models import (
    EmployeeModel, PayPeriodModel, TimeEntryModel, LeaveRecordModel,
    AllowanceModel, DeductionModel, PayrollInputModel, ExceptionModel,
    ValidationRuleModel
)
from src.config import (
    ISSUE_HOURS_EXCEED_MAX, ISSUE_DUPLICATE_ALLOWANCE, ISSUE_UNAPPROVED_TIME,
    ISSUE_DOUBLE_LEAVE_DEDUCTION, ISSUE_RECONCILIATION_MISMATCH, ISSUE_MISSING_BANK_TAX
)

class ValidationEngine:
    def __init__(self, data: Dict[str, Any]):
        self.employees: List[EmployeeModel] = data["employees"]
        self.pay_periods: List[PayPeriodModel] = data["pay_periods"]
        self.time_entries: List[TimeEntryModel] = data["time_entries"]
        self.leave_records: List[LeaveRecordModel] = data["leave_records"]
        self.allowances: List[AllowanceModel] = data["allowances"]
        self.deductions: List[DeductionModel] = data["deductions"]
        self.payroll_inputs: List[PayrollInputModel] = data["payroll_inputs"]
        
        self.exceptions: List[ExceptionModel] = []
        self._exception_counter = 0

    def run_all_validations(self) -> List[ExceptionModel]:
        """Runs all 6 business validation and compliance rules."""
        self.exceptions = []
        self._exception_counter = 0

        # Build fast lookup maps
        emp_map = {e.employee_id: e for e in self.employees}
        
        # 1. Check Missing Bank/Tax Compliance (RULE-006)
        self._validate_compliance(emp_map)

        # 2. Check Time Entries (RULE-001 Hours Exceed & RULE-003 Unapproved)
        self._validate_time_entries()

        # 3. Check Allowances for Duplicates (RULE-002)
        self._validate_allowances()

        # 4. Check Deductions for Double Leave Debits (RULE-004)
        self._validate_deductions()

        # 5. Check PayrollInput Arithmetic Reconciliation (RULE-005 & overall status)
        self._validate_reconciliation_and_hours()

        return self.exceptions

    def _next_exc_id(self, period_id: str) -> str:
        self._exception_counter += 1
        return f"EXC-{period_id}-{self._exception_counter:06d}"

    def _validate_compliance(self, emp_map: Dict[str, EmployeeModel]):
        """RULE-006: Check for missing bank or tax info on active employees."""
        for pin in self.payroll_inputs:
            emp = emp_map.get(pin.employee_id)
            if not emp:
                continue
            if not emp.bank_account_no or not emp.tax_identifier or not emp.bank_ifsc:
                self.exceptions.append(ExceptionModel(
                    exception_id=self._next_exc_id(pin.pay_period_id),
                    rule_id="RULE-006",
                    entity_type="Employee",
                    entity_id=emp.employee_id,
                    employee_id=emp.employee_id,
                    pay_period_id=pin.pay_period_id,
                    issue_type=ISSUE_MISSING_BANK_TAX,
                    status="OPEN",
                    details=f'{{"reason": "Missing bank account or tax ID", "employee_id": "{emp.employee_id}"}}',
                    created_at=datetime.now(timezone.utc).isoformat()
                ))

    def _validate_time_entries(self):
        """RULE-003: Check for unapproved time entries."""
        for t in self.time_entries:
            if t.status != "APPROVED":
                self.exceptions.append(ExceptionModel(
                    exception_id=self._next_exc_id(t.pay_period_id),
                    rule_id="RULE-003",
                    entity_type="TimeEntry",
                    entity_id=t.time_entry_id,
                    employee_id=t.employee_id,
                    pay_period_id=t.pay_period_id,
                    issue_type=ISSUE_UNAPPROVED_TIME,
                    status="OPEN",
                    details=f'{{"time_entry_id": "{t.time_entry_id}", "status": "{t.status}"}}',
                    created_at=datetime.now(timezone.utc).isoformat()
                ))

    def _validate_allowances(self):
        """RULE-002: Detect duplicate allowances in the same pay period."""
        seen: Dict[Tuple[str, str, str], str] = {}
        for a in self.allowances:
            key = (a.employee_id, a.pay_period_id, a.allowance_type)
            if key in seen:
                self.exceptions.append(ExceptionModel(
                    exception_id=self._next_exc_id(a.pay_period_id),
                    rule_id="RULE-002",
                    entity_type="Allowance",
                    entity_id=a.allowance_id,
                    employee_id=a.employee_id,
                    pay_period_id=a.pay_period_id,
                    issue_type=ISSUE_DUPLICATE_ALLOWANCE,
                    status="OPEN",
                    details=f'{{"allowance_id": "{a.allowance_id}", "duplicate_type": "{a.allowance_type}", "original_id": "{seen[key]}"}}',
                    created_at=datetime.now(timezone.utc).isoformat()
                ))
            else:
                seen[key] = a.allowance_id

    def _validate_deductions(self):
        """RULE-004: Detect double deductions for the same leave record."""
        seen_leave_deductions: Dict[str, str] = {}
        for d in self.deductions:
            if d.source_ref_id and d.source_ref_id.startswith("LEV-"):
                if d.source_ref_id in seen_leave_deductions:
                    self.exceptions.append(ExceptionModel(
                        exception_id=self._next_exc_id(d.pay_period_id),
                        rule_id="RULE-004",
                        entity_type="Deduction",
                        entity_id=d.deduction_id,
                        employee_id=d.employee_id,
                        pay_period_id=d.pay_period_id,
                        issue_type=ISSUE_DOUBLE_LEAVE_DEDUCTION,
                        status="OPEN",
                        details=f'{{"deduction_id": "{d.deduction_id}", "duplicated_source_ref": "{d.source_ref_id}", "original_id": "{seen_leave_deductions[d.source_ref_id]}"}}',
                        created_at=datetime.now(timezone.utc).isoformat()
                    ))
                else:
                    seen_leave_deductions[d.source_ref_id] = d.deduction_id

    def _validate_reconciliation_and_hours(self):
        """
        RULE-001 (Hours Threshold) and RULE-005 (Arithmetic Reconciliation).
        Also sets PayrollInput lifecycle state to FLAGGED or VALIDATED.
        """
        # Index exceptions by (employee_id, pay_period_id)
        flagged_keys = {(e.employee_id, e.pay_period_id) for e in self.exceptions}

        for pin in self.payroll_inputs:
            key = (pin.employee_id, pin.pay_period_id)
            has_error = (key in flagged_keys)

            # Check Total Hours Exceed Maximum (> 200h)
            total_hours = pin.regular_hours + pin.overtime_hours
            if total_hours > 200.0:
                has_error = True
                self.exceptions.append(ExceptionModel(
                    exception_id=self._next_exc_id(pin.pay_period_id),
                    rule_id="RULE-001",
                    entity_type="PayrollInput",
                    entity_id=pin.payroll_input_id,
                    employee_id=pin.employee_id,
                    pay_period_id=pin.pay_period_id,
                    issue_type=ISSUE_HOURS_EXCEED_MAX,
                    status="OPEN",
                    details=f'{{"total_hours": {total_hours:.2f}, "max_threshold": 200.0}}',
                    created_at=datetime.now(timezone.utc).isoformat()
                ))

            # Check Arithmetic Reconciliation
            expected_gross = round(pin.base_earnings + pin.overtime_earnings + pin.total_allowance, 2)
            variance = round(abs(pin.gross_pay - expected_gross), 2)
            pin.reconciliation_variance = round(pin.gross_pay - expected_gross, 2)

            if variance > 0.01:
                has_error = True
                self.exceptions.append(ExceptionModel(
                    exception_id=self._next_exc_id(pin.pay_period_id),
                    rule_id="RULE-005",
                    entity_type="PayrollInput",
                    entity_id=pin.payroll_input_id,
                    employee_id=pin.employee_id,
                    pay_period_id=pin.pay_period_id,
                    issue_type=ISSUE_RECONCILIATION_MISMATCH,
                    status="OPEN",
                    details=f'{{"gross_pay": {pin.gross_pay}, "expected_gross": {expected_gross}, "variance": {pin.reconciliation_variance}}}',
                    created_at=datetime.now(timezone.utc).isoformat()
                ))

            # Set lifecycle state
            if has_error:
                pin.status = "FLAGGED"
            else:
                pin.status = "VALIDATED"
