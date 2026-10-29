-- ============================================================================
-- Payroll Validation & Reconciliation Engine — Database Schema (DDL)
-- Compliant with SQLite, PostgreSQL, and MySQL conventions.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- 1. Master: PayGroup
CREATE TABLE IF NOT EXISTS pay_groups (
    pay_group_id VARCHAR(16) PRIMARY KEY,
    name VARCHAR(64) NOT NULL UNIQUE,
    frequency VARCHAR(16) NOT NULL CHECK(frequency IN ('MONTHLY', 'BI_WEEKLY')),
    standard_hours DECIMAL(6,2) NOT NULL DEFAULT 160.00,
    max_overtime_hours DECIMAL(5,2) NOT NULL DEFAULT 40.00,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- 2. Master: PayPeriod
CREATE TABLE IF NOT EXISTS pay_periods (
    pay_period_id VARCHAR(16) PRIMARY KEY,
    pay_group_id VARCHAR(16) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    cut_off_date DATE NOT NULL,
    status VARCHAR(16) NOT NULL CHECK(status IN ('OPEN', 'PROCESSING', 'CLOSED')),
    FOREIGN KEY (pay_group_id) REFERENCES pay_groups(pay_group_id),
    CHECK(start_date <= end_date),
    CHECK(end_date <= cut_off_date)
);

-- 3. Master: Employee
CREATE TABLE IF NOT EXISTS employees (
    employee_id VARCHAR(16) PRIMARY KEY,
    pay_group_id VARCHAR(16) NOT NULL,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    bank_account_no VARCHAR(32),
    bank_ifsc VARCHAR(16),
    tax_identifier VARCHAR(20),
    hourly_rate DECIMAL(8,2) NOT NULL CHECK(hourly_rate > 0),
    status VARCHAR(16) NOT NULL CHECK(status IN ('ACTIVE', 'ON_LEAVE', 'TERMINATED')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pay_group_id) REFERENCES pay_groups(pay_group_id)
);

-- 4. Transaction: TimeEntry
CREATE TABLE IF NOT EXISTS time_entries (
    time_entry_id VARCHAR(32) PRIMARY KEY,
    employee_id VARCHAR(16) NOT NULL,
    pay_period_id VARCHAR(16) NOT NULL,
    work_date DATE NOT NULL,
    regular_hours DECIMAL(4,2) NOT NULL DEFAULT 8.00,
    overtime_hours DECIMAL(4,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(16) NOT NULL CHECK(status IN ('SUBMITTED', 'APPROVED', 'REJECTED')),
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (pay_period_id) REFERENCES pay_periods(pay_period_id),
    CHECK(regular_hours >= 0 AND regular_hours <= 16),
    CHECK(overtime_hours >= 0 AND overtime_hours <= 8)
);

CREATE INDEX IF NOT EXISTS idx_time_emp_period ON time_entries(employee_id, pay_period_id);

-- 5. Transaction: LeaveRecord
CREATE TABLE IF NOT EXISTS leave_records (
    leave_record_id VARCHAR(32) PRIMARY KEY,
    employee_id VARCHAR(16) NOT NULL,
    pay_period_id VARCHAR(16) NOT NULL,
    leave_date DATE NOT NULL,
    leave_type VARCHAR(16) NOT NULL CHECK(leave_type IN ('PAID_CASUAL', 'PAID_SICK', 'UNPAID_LOP')),
    hours_deducted DECIMAL(4,2) NOT NULL DEFAULT 8.00,
    status VARCHAR(16) NOT NULL CHECK(status IN ('APPROVED', 'PENDING', 'REJECTED')),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (pay_period_id) REFERENCES pay_periods(pay_period_id)
);

-- 6. Transaction: Allowance
CREATE TABLE IF NOT EXISTS allowances (
    allowance_id VARCHAR(40) PRIMARY KEY,
    employee_id VARCHAR(16) NOT NULL,
    pay_period_id VARCHAR(16) NOT NULL,
    allowance_type VARCHAR(24) NOT NULL CHECK(allowance_type IN ('HOUSING', 'CONVEYANCE', 'MEAL_STIPEND', 'SHIFT_ALLOWANCE')),
    amount DECIMAL(8,2) NOT NULL CHECK(amount > 0),
    is_taxable INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (pay_period_id) REFERENCES pay_periods(pay_period_id)
);

-- 7. Transaction: Deduction
CREATE TABLE IF NOT EXISTS deductions (
    deduction_id VARCHAR(40) PRIMARY KEY,
    employee_id VARCHAR(16) NOT NULL,
    pay_period_id VARCHAR(16) NOT NULL,
    deduction_type VARCHAR(24) NOT NULL CHECK(deduction_type IN ('PROVIDENT_FUND', 'PROFESSIONAL_TAX', 'UNPAID_LEAVE', 'HEALTH_INSURANCE')),
    amount DECIMAL(8,2) NOT NULL CHECK(amount > 0),
    source_ref_id VARCHAR(32),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (pay_period_id) REFERENCES pay_periods(pay_period_id)
);

-- 8. Core Aggregation: PayrollInput
CREATE TABLE IF NOT EXISTS payroll_inputs (
    payroll_input_id VARCHAR(32) PRIMARY KEY,
    employee_id VARCHAR(16) NOT NULL,
    pay_period_id VARCHAR(16) NOT NULL,
    regular_hours DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    overtime_hours DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    base_earnings DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    overtime_earnings DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_allowance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_deduction DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    gross_pay DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    net_pay DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    reconciliation_variance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status VARCHAR(24) NOT NULL CHECK(status IN ('DRAFT', 'VALIDATED', 'FLAGGED', 'APPROVED', 'EXPORTED')),
    aggregated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (pay_period_id) REFERENCES pay_periods(pay_period_id),
    UNIQUE(employee_id, pay_period_id)
);

-- 9. Configuration: ValidationRule
CREATE TABLE IF NOT EXISTS validation_rules (
    rule_id VARCHAR(16) PRIMARY KEY,
    rule_name VARCHAR(64) NOT NULL UNIQUE,
    category VARCHAR(24) NOT NULL,
    severity VARCHAR(16) NOT NULL CHECK(severity IN ('CRITICAL_BLOCKER', 'WARNING')),
    description TEXT NOT NULL
);

-- 10. Incident / Audit: Exception
CREATE TABLE IF NOT EXISTS exceptions (
    exception_id VARCHAR(32) PRIMARY KEY,
    rule_id VARCHAR(16) NOT NULL,
    entity_type VARCHAR(24) NOT NULL,
    entity_id VARCHAR(40) NOT NULL,
    employee_id VARCHAR(16) NOT NULL,
    pay_period_id VARCHAR(16) NOT NULL,
    issue_type VARCHAR(32) NOT NULL,
    status VARCHAR(16) NOT NULL CHECK(status IN ('OPEN', 'RESOLVED', 'OVERRIDDEN')),
    details TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES validation_rules(rule_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (pay_period_id) REFERENCES pay_periods(pay_period_id)
);

-- 11. Sign-off: Approval
CREATE TABLE IF NOT EXISTS approvals (
    approval_id VARCHAR(32) PRIMARY KEY,
    payroll_input_id VARCHAR(32) NOT NULL,
    approver_role VARCHAR(24) NOT NULL CHECK(approver_role IN ('MANAGER', 'HR_PARTNER', 'FINANCE_CONTROLLER')),
    approver_id VARCHAR(32) NOT NULL,
    decision VARCHAR(16) NOT NULL CHECK(decision IN ('APPROVED', 'REJECTED', 'REVISION_REQUESTED')),
    comments TEXT,
    decided_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (payroll_input_id) REFERENCES payroll_inputs(payroll_input_id)
);

-- 12. Final Delivery: PayrollExport
CREATE TABLE IF NOT EXISTS payroll_exports (
    export_id VARCHAR(32) PRIMARY KEY,
    payroll_input_id VARCHAR(32) NOT NULL UNIQUE,
    pay_period_id VARCHAR(16) NOT NULL,
    employee_id VARCHAR(16) NOT NULL,
    bank_account_no VARCHAR(32) NOT NULL,
    approved_gross DECIMAL(10,2) NOT NULL,
    approved_net DECIMAL(10,2) NOT NULL,
    reconciliation_hash VARCHAR(64) NOT NULL,
    export_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (payroll_input_id) REFERENCES payroll_inputs(payroll_input_id),
    FOREIGN KEY (pay_period_id) REFERENCES pay_periods(pay_period_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- Seed Default Validation Rules
INSERT OR IGNORE INTO validation_rules (rule_id, rule_name, category, severity, description) VALUES
('RULE-001', 'Hours Exceed Period Maximum', 'HOURS_THRESHOLD', 'CRITICAL_BLOCKER', 'Flags employees whose total work hours exceed policy limits (>200h/month or >16h/day)'),
('RULE-002', 'Duplicate Allowance Entry', 'DUPLICATE_CHECK', 'CRITICAL_BLOCKER', 'Identifies redundant duplicate allowance postings for the same worker in a single pay cycle'),
('RULE-003', 'Unapproved Time Entry Ingestion', 'COMPLIANCE', 'CRITICAL_BLOCKER', 'Detects timesheet entries without managerial approval attempting to enter payroll aggregation'),
('RULE-004', 'Double Leave Deduction Anomaly', 'RECONCILIATION', 'CRITICAL_BLOCKER', 'Flags identical leave events deducted more than once from gross compensation'),
('RULE-005', 'Payroll Arithmetic Reconciliation', 'RECONCILIATION', 'CRITICAL_BLOCKER', 'Verifies that gross_pay exactly equals base_earnings + overtime_earnings + allowances - deductions'),
('RULE-006', 'Missing Banking or Tax Identification', 'COMPLIANCE', 'CRITICAL_BLOCKER', 'Prevents disbursement to active employees lacking bank account numbers or tax identification');
