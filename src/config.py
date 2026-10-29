"""
Configuration constants and parameters for the Payroll Validation Engine.
"""

# Default deterministic seed specified by the problem statement
DEFAULT_SEED = 20261022

# Scale definitions
SCALES = {
    "starter": {
        "num_employees": 50,
        "num_months": 1,
        "year": 2026,
        "anomaly_rate": 0.08, # 8% planted anomalies
    },
    "medium": {
        "num_employees": 500,
        "num_months": 2,
        "year": 2026,
        "anomaly_rate": 0.05,
    },
    "full": {
        "num_employees": 3000,
        "num_months": 3,
        "year": 2026,
        "anomaly_rate": 0.04,
    }
}

# Standard Pay Groups
PAY_GROUPS = [
    {
        "id": "PG-TECH",
        "name": "Technology & Product",
        "frequency": "MONTHLY",
        "standard_hours": 160.0,
        "max_overtime_hours": 40.0,
    },
    {
        "id": "PG-OPS",
        "name": "Operations & Support",
        "frequency": "MONTHLY",
        "standard_hours": 160.0,
        "max_overtime_hours": 30.0,
    },
    {
        "id": "PG-EXEC",
        "name": "Executive & Leadership",
        "frequency": "MONTHLY",
        "standard_hours": 160.0,
        "max_overtime_hours": 10.0,
    }
]

# Allowance Types & standard monthly ranges
ALLOWANCE_TYPES = ["HOUSING", "CONVEYANCE", "MEAL_STIPEND", "SHIFT_ALLOWANCE"]

# Deduction Types
DEDUCTION_TYPES = ["PROVIDENT_FUND", "PROFESSIONAL_TAX", "UNPAID_LEAVE", "HEALTH_INSURANCE"]

# Issue Types / Anomaly ground truth labels
ISSUE_HOURS_EXCEED_MAX = "HOURS_EXCEED_MAXIMUM"
ISSUE_DUPLICATE_ALLOWANCE = "DUPLICATE_ALLOWANCE"
ISSUE_UNAPPROVED_TIME = "UNAPPROVED_TIME_EXPORTED"
ISSUE_DOUBLE_LEAVE_DEDUCTION = "DOUBLE_LEAVE_DEDUCTION"
ISSUE_RECONCILIATION_MISMATCH = "RECONCILIATION_MISMATCH"
ISSUE_MISSING_BANK_TAX = "MISSING_BANK_TAX"

ALL_ISSUES = [
    ISSUE_HOURS_EXCEED_MAX,
    ISSUE_DUPLICATE_ALLOWANCE,
    ISSUE_UNAPPROVED_TIME,
    ISSUE_DOUBLE_LEAVE_DEDUCTION,
    ISSUE_RECONCILIATION_MISMATCH,
    ISSUE_MISSING_BANK_TAX
]
