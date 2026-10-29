"""
Unit Tests for Business Validation Rules.
Verifies that all 6 rules correctly flag planted anomalies and negative scenarios.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models import (
    EmployeeModel, PayPeriodModel, TimeEntryModel, AllowanceModel,
    DeductionModel, PayrollInputModel
)
from src.validator import ValidationEngine
from src.config import (
    ISSUE_HOURS_EXCEED_MAX, ISSUE_DUPLICATE_ALLOWANCE, ISSUE_UNAPPROVED_TIME,
    ISSUE_DOUBLE_LEAVE_DEDUCTION, ISSUE_RECONCILIATION_MISMATCH, ISSUE_MISSING_BANK_TAX
)

class TestValidationRules(unittest.TestCase):
    def test_rule_001_hours_exceed(self):
        data = {
            "employees": [EmployeeModel("EMP-001", "PG-TECH", "Test", "User", "test@test.com", 500.0, "12345", "IFSC01", "TAX01")],
            "pay_periods": [PayPeriodModel("PP-2026-01", "PG-TECH", "2026-01-01", "2026-01-31", "2026-01-31")],
            "time_entries": [],
            "leave_records": [],
            "allowances": [],
            "deductions": [],
            "payroll_inputs": [
                PayrollInputModel("PIN-EMP-001-PP-2026-01", "EMP-001", "PP-2026-01", regular_hours=160.0, overtime_hours=45.0, gross_pay=113750.0, base_earnings=80000.0, overtime_earnings=33750.0)
            ]
        }
        val = ValidationEngine(data)
        exceptions = val.run_all_validations()
        
        issue_types = [e.issue_type for e in exceptions]
        self.assertIn(ISSUE_HOURS_EXCEED_MAX, issue_types)

    def test_rule_002_duplicate_allowance(self):
        data = {
            "employees": [EmployeeModel("EMP-001", "PG-TECH", "Test", "User", "test@test.com", 500.0, "12345", "IFSC01", "TAX01")],
            "pay_periods": [PayPeriodModel("PP-2026-01", "PG-TECH", "2026-01-01", "2026-01-31", "2026-01-31")],
            "time_entries": [],
            "leave_records": [],
            "allowances": [
                AllowanceModel("ALW-01", "EMP-001", "PP-2026-01", "HOUSING", 8000.0),
                AllowanceModel("ALW-02", "EMP-001", "PP-2026-01", "HOUSING", 8000.0)
            ],
            "deductions": [],
            "payroll_inputs": []
        }
        val = ValidationEngine(data)
        exceptions = val.run_all_validations()
        
        issue_types = [e.issue_type for e in exceptions]
        self.assertIn(ISSUE_DUPLICATE_ALLOWANCE, issue_types)

    def test_rule_003_unapproved_time(self):
        data = {
            "employees": [EmployeeModel("EMP-001", "PG-TECH", "Test", "User", "test@test.com", 500.0, "12345", "IFSC01", "TAX01")],
            "pay_periods": [PayPeriodModel("PP-2026-01", "PG-TECH", "2026-01-01", "2026-01-31", "2026-01-31")],
            "time_entries": [
                TimeEntryModel("TIME-01", "EMP-001", "PP-2026-01", "2026-01-05", 8.0, 0.0, status="SUBMITTED")
            ],
            "leave_records": [],
            "allowances": [],
            "deductions": [],
            "payroll_inputs": []
        }
        val = ValidationEngine(data)
        exceptions = val.run_all_validations()
        
        issue_types = [e.issue_type for e in exceptions]
        self.assertIn(ISSUE_UNAPPROVED_TIME, issue_types)

    def test_rule_004_double_leave_deduction(self):
        data = {
            "employees": [EmployeeModel("EMP-001", "PG-TECH", "Test", "User", "test@test.com", 500.0, "12345", "IFSC01", "TAX01")],
            "pay_periods": [PayPeriodModel("PP-2026-01", "PG-TECH", "2026-01-01", "2026-01-31", "2026-01-31")],
            "time_entries": [],
            "leave_records": [],
            "allowances": [],
            "deductions": [
                DeductionModel("DED-01", "EMP-001", "PP-2026-01", "UNPAID_LEAVE", 4000.0, source_ref_id="LEV-2026-01-10"),
                DeductionModel("DED-02", "EMP-001", "PP-2026-01", "UNPAID_LEAVE", 4000.0, source_ref_id="LEV-2026-01-10")
            ],
            "payroll_inputs": []
        }
        val = ValidationEngine(data)
        exceptions = val.run_all_validations()
        
        issue_types = [e.issue_type for e in exceptions]
        self.assertIn(ISSUE_DOUBLE_LEAVE_DEDUCTION, issue_types)

    def test_rule_005_reconciliation_mismatch(self):
        data = {
            "employees": [EmployeeModel("EMP-001", "PG-TECH", "Test", "User", "test@test.com", 500.0, "12345", "IFSC01", "TAX01")],
            "pay_periods": [PayPeriodModel("PP-2026-01", "PG-TECH", "2026-01-01", "2026-01-31", "2026-01-31")],
            "time_entries": [],
            "leave_records": [],
            "allowances": [],
            "deductions": [],
            "payroll_inputs": [
                # Base 80k + Allowance 0 = 80k, but gross corrupted to 85k!
                PayrollInputModel("PIN-EMP-001-PP-2026-01", "EMP-001", "PP-2026-01", regular_hours=160.0, base_earnings=80000.0, gross_pay=85000.0)
            ]
        }
        val = ValidationEngine(data)
        exceptions = val.run_all_validations()
        
        issue_types = [e.issue_type for e in exceptions]
        self.assertIn(ISSUE_RECONCILIATION_MISMATCH, issue_types)

    def test_rule_006_missing_bank_tax(self):
        data = {
            "employees": [EmployeeModel("EMP-002", "PG-TECH", "NoBank", "User", "nobank@test.com", 500.0, bank_account_no=None, bank_ifsc=None, tax_identifier=None)],
            "pay_periods": [PayPeriodModel("PP-2026-01", "PG-TECH", "2026-01-01", "2026-01-31", "2026-01-31")],
            "time_entries": [],
            "leave_records": [],
            "allowances": [],
            "deductions": [],
            "payroll_inputs": [
                PayrollInputModel("PIN-EMP-002-PP-2026-01", "EMP-002", "PP-2026-01", regular_hours=160.0, base_earnings=80000.0, gross_pay=80000.0)
            ]
        }
        val = ValidationEngine(data)
        exceptions = val.run_all_validations()
        
        issue_types = [e.issue_type for e in exceptions]
        self.assertIn(ISSUE_MISSING_BANK_TAX, issue_types)

if __name__ == "__main__":
    unittest.main()
