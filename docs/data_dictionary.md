# Payroll Validation & Reconciliation Engine — Data Dictionary

## 1. Overview
This data dictionary defines the complete schema for the 12 core entities of the Payroll Pre-Export Validation and Reconciliation system for Yottaflex.

Cardinality conventions: `1:1` (One-to-One), `1:N` (One-to-Many), `N:M` (Many-to-Many via bridge/transaction records).

---

## 2. Master Data Entities

### 2.1 PayGroup
*Represents a payroll categorization calendar (e.g., Engineering, Operations, Executive).*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `pay_group_id` | VARCHAR(16) | Yes | `PG-TECH`, `PG-OPS`, `PG-EXEC` | Code | PK | Primary Key. Immutable identifier. |
| `name` | VARCHAR(64) | Yes | Non-empty text | Text | Unique | Human-readable division title. |
| `frequency` | VARCHAR(16) | Yes | `MONTHLY`, `BI_WEEKLY` | Enum | No | Payroll calculation frequency. |
| `standard_hours` | DECIMAL(6,2)| Yes | 80.00 – 180.00 | Hours | No | Baseline standard hours per cycle. |
| `max_overtime_hours`| DECIMAL(5,2)| Yes| 0.00 – 60.00 | Hours | No | Max allowable overtime hours. |
| `is_active` | BOOLEAN | Yes | `TRUE`, `FALSE` | Flag | No | Whether the group is currently active. |

---

### 2.2 PayPeriod
*Represents a distinct calendar cycle for payroll processing.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `pay_period_id` | VARCHAR(16) | Yes | `PP-YYYY-MM` (e.g. `PP-2026-01`)| Code | PK | Primary Key. Deterministic period ID. |
| `pay_group_id` | VARCHAR(16) | Yes | FK $\rightarrow$ `PayGroup.pay_group_id` | Code | No | Parent pay group. |
| `start_date` | DATE | Yes | YYYY-MM-DD | Date | No | Beginning of period (`start_date <= end_date`). |
| `end_date` | DATE | Yes | YYYY-MM-DD | Date | No | End of period. |
| `cut_off_date` | DATE | Yes | YYYY-MM-DD | Date | No | Submission cutoff (`end_date <= cut_off_date`). |
| `status` | VARCHAR(16) | Yes | `OPEN`, `PROCESSING`, `CLOSED` | Enum | No | State machine for processing stage. |

---

### 2.3 Employee
*Represents an individual worker master record.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `employee_id` | VARCHAR(16) | Yes | `EMP-000001` to `EMP-999999` | Code | PK | Primary Key zero-padded deterministic. |
| `pay_group_id` | VARCHAR(16) | Yes | FK $\rightarrow$ `PayGroup.pay_group_id` | Code | No | Associated pay schedule. |
| `first_name` | VARCHAR(64) | Yes | Non-empty alphabetic string | Text | No | Employee given name. |
| `last_name` | VARCHAR(64) | Yes | Non-empty alphabetic string | Text | No | Employee family name. |
| `email` | VARCHAR(128)| Yes | Valid RFC email | Text | Unique | Unique work email address. |
| `bank_account_no`| VARCHAR(32) | No | 8-18 digits or `NULL` | Digits| No | Bank account (Validation checks non-null). |
| `bank_ifsc` | VARCHAR(16) | No | 11-char alphanumeric or `NULL` | Code | No | Bank IFSC routing code. |
| `tax_identifier`| VARCHAR(20) | No | 10-char alphanumeric or `NULL` | Code | No | Tax ID (e.g. PAN/SSN). |
| `hourly_rate` | DECIMAL(8,2)| Yes | 150.00 – 3500.00 | Currency (INR/USD) | No | Base hourly compensation rate. |
| `status` | VARCHAR(16) | Yes | `ACTIVE`, `ON_LEAVE`, `TERMINATED`| Enum | No | Employment lifecycle state. |
| `created_at` | TIMESTAMP | Yes | ISO 8601 string | Time | No | Master creation timestamp. |

---

## 3. Transaction & Event Entities

### 3.1 TimeEntry
*Daily timesheet records submitted by workers.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `time_entry_id`| VARCHAR(32) | Yes | `TIME-<employee-id>-<date>` | Code | PK | Primary Key. Daily unique time entry. |
| `employee_id` | VARCHAR(16) | Yes | FK $\rightarrow$ `Employee.employee_id` | Code | No | Submitting employee. |
| `pay_period_id`| VARCHAR(16) | Yes | FK $\rightarrow$ `PayPeriod.pay_period_id`| Code | No | Applicable pay period. |
| `work_date` | DATE | Yes | YYYY-MM-DD within period | Date | No | Date worked. |
| `regular_hours`| DECIMAL(4,2)| Yes | 0.00 to 12.00 | Hours | No | Base daily work hours. |
| `overtime_hours`| DECIMAL(4,2)| Yes| 0.00 to 8.00 | Hours | No | Overtime daily work hours. |
| `status` | VARCHAR(16) | Yes | `SUBMITTED`, `APPROVED`, `REJECTED` | Enum | No | Approval status; only `APPROVED` can export. |
| `version` | INTEGER | Yes | $\ge 1$ | Int | No | Optimistic lock & correction audit counter. |

---

### 3.2 LeaveRecord
*Leave applications affecting working hours and compensation.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `leave_record_id`| VARCHAR(32)| Yes | `LEV-<employee-id>-<date>` | Code | PK | Primary Key. |
| `employee_id` | VARCHAR(16) | Yes | FK $\rightarrow$ `Employee.employee_id` | Code | No | Applying employee. |
| `pay_period_id`| VARCHAR(16) | Yes | FK $\rightarrow$ `PayPeriod.pay_period_id`| Code | No | Applicable period. |
| `leave_date` | DATE | Yes | YYYY-MM-DD | Date | No | Date of absence. |
| `leave_type` | VARCHAR(16) | Yes | `PAID_CASUAL`, `PAID_SICK`, `UNPAID_LOP` | Enum | No | Type of leave. |
| `hours_deducted`| DECIMAL(4,2)| Yes| 4.00 or 8.00 | Hours | No | Standard absence duration. |
| `status` | VARCHAR(16) | Yes | `APPROVED`, `PENDING`, `REJECTED` | Enum | No | Only approved unpaid leave creates deduction. |

---

### 3.3 Allowance
*Discretionary and recurring benefits credited to employee.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `allowance_id` | VARCHAR(40) | Yes | `ALW-<employee-id>-<period>-<seq>` | Code | PK | Primary Key. |
| `employee_id` | VARCHAR(16) | Yes | FK $\rightarrow$ `Employee.employee_id` | Code | No | Beneficiary. |
| `pay_period_id`| VARCHAR(16) | Yes | FK $\rightarrow$ `PayPeriod.pay_period_id`| Code | No | Allocation period. |
| `allowance_type`| VARCHAR(24) | Yes | `HOUSING`, `CONVEYANCE`, `MEAL_STIPEND`, `SHIFT_ALLOWANCE` | Enum | No | Allowance classification. |
| `amount` | DECIMAL(8,2)| Yes | > 0.00 | Currency | No | Credit amount. |
| `is_taxable` | BOOLEAN | Yes | `TRUE`, `FALSE` | Flag | No | Tax treatment flag. |

---

### 3.4 Deduction
*Statutory and discretionary withholdings debited from gross compensation.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `deduction_id` | VARCHAR(40) | Yes | `DED-<employee-id>-<period>-<seq>` | Code | PK | Primary Key. |
| `employee_id` | VARCHAR(16) | Yes | FK $\rightarrow$ `Employee.employee_id` | Code | No | Deducted employee. |
| `pay_period_id`| VARCHAR(16) | Yes | FK $\rightarrow$ `PayPeriod.pay_period_id`| Code | No | Deduction period. |
| `deduction_type`| VARCHAR(24) | Yes | `PROVIDENT_FUND`, `PROFESSIONAL_TAX`, `UNPAID_LEAVE`, `HEALTH_INSURANCE` | Enum | No | Category. |
| `amount` | DECIMAL(8,2)| Yes | > 0.00 | Currency | No | Debit amount. |
| `source_ref_id`| VARCHAR(32) | No | Refers to `leave_record_id` or `POLICY` | Code | No | Audit traceability to root event. |

---

## 4. Aggregation, Validation & Control Entities

### 4.1 PayrollInput
*Consolidated pre-export payroll record per employee per cycle.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `payroll_input_id`| VARCHAR(32)| Yes | `PIN-<employee-id>-<period>` | Code | PK | Deterministic composite key. |
| `employee_id` | VARCHAR(16) | Yes | FK $\rightarrow$ `Employee.employee_id` | Code | No | Target employee. |
| `pay_period_id`| VARCHAR(16) | Yes | FK $\rightarrow$ `PayPeriod.pay_period_id`| Code | No | Target period. |
| `regular_hours`| DECIMAL(6,2)| Yes | Sum of approved TimeEntry regular hours | Hours | No | Aggregated hours. |
| `overtime_hours`| DECIMAL(6,2)| Yes| Sum of approved TimeEntry overtime hours | Hours | No | Aggregated overtime. |
| `base_earnings`| DECIMAL(10,2)| Yes| `regular_hours * hourly_rate` | Currency | No | Mathematical derivation. |
| `overtime_earnings`| DECIMAL(10,2)| Yes| `overtime_hours * hourly_rate * 1.5` | Currency | No | Overtime premium. |
| `total_allowance`| DECIMAL(10,2)| Yes| Sum of allowances | Currency | No | Total additions. |
| `total_deduction`| DECIMAL(10,2)| Yes| Sum of deductions | Currency | No | Total subtractions. |
| `gross_pay` | DECIMAL(10,2)| Yes | `base_earnings + overtime_earnings + total_allowance` | Currency | No | Subject to reconciliation. |
| `net_pay` | DECIMAL(10,2)| Yes | `gross_pay - total_deduction` | Currency | No | Net payable to worker. |
| `reconciliation_variance`| DECIMAL(10,2)| Yes | Must be `0.00` for valid export | Currency | No | Arithmetic verification. |
| `status` | VARCHAR(24) | Yes | `DRAFT`, `VALIDATED`, `FLAGGED`, `APPROVED`, `EXPORTED` | Enum | No | Lifecycle control state. |

---

### 4.2 ValidationRule
*Master repository of active business compliance checks.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `rule_id` | VARCHAR(16) | Yes | `RULE-001` to `RULE-999` | Code | PK | Stable rule identifier. |
| `rule_name` | VARCHAR(64) | Yes | Descriptive title | Text | Unique | Human-readable check title. |
| `category` | VARCHAR(24) | Yes | `COMPLIANCE`, `HOURS_THRESHOLD`, `DUPLICATE_CHECK`, `RECONCILIATION` | Enum | No | Functional grouping. |
| `severity` | VARCHAR(16) | Yes | `CRITICAL_BLOCKER`, `WARNING` | Enum | No | Failure impact level. |
| `description` | TEXT | Yes | Prose explanation | Text | No | What this rule verifies. |

---

### 4.3 Exception
*Audit log of detected business rule violations and planted anomalies.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `exception_id` | VARCHAR(32) | Yes | `EXC-<period>-<seq>` | Code | PK | Unique exception incident. |
| `rule_id` | VARCHAR(16) | Yes | FK $\rightarrow$ `ValidationRule.rule_id` | Code | No | Violated rule. |
| `entity_type` | VARCHAR(24) | Yes | `PAYROLL_INPUT`, `TIME_ENTRY`, `ALLOWANCE`, `DEDUCTION`, `EMPLOYEE` | Enum | No | Target entity table. |
| `entity_id` | VARCHAR(40) | Yes | Reference to target entity PK | Code | No | Foreign entity identifier. |
| `employee_id` | VARCHAR(16) | Yes | FK $\rightarrow$ `Employee.employee_id` | Code | No | Impacted employee. |
| `pay_period_id`| VARCHAR(16) | Yes | FK $\rightarrow$ `PayPeriod.pay_period_id`| Code | No | Impacted period. |
| `issue_type` | VARCHAR(32) | Yes | Standardized issue code | Code | No | Ground-truth classification. |
| `status` | VARCHAR(16) | Yes | `OPEN`, `RESOLVED`, `OVERRIDDEN` | Enum | No | Exception resolution state. |
| `details` | TEXT (JSON) | Yes | Serialized JSON context | Text | No | Diagnostic details. |
| `created_at` | TIMESTAMP | Yes | ISO 8601 string | Time | No | Logging timestamp. |

---

### 4.4 Approval
*Auditable authorization sign-off by HR, Managers, or Finance.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `approval_id` | VARCHAR(32) | Yes | `APP-<seq>` | Code | PK | Primary Key. |
| `payroll_input_id`| VARCHAR(32)| Yes | FK $\rightarrow$ `PayrollInput.payroll_input_id` | Code | No | Authorized payroll line. |
| `approver_role`| VARCHAR(24) | Yes | `MANAGER`, `HR_PARTNER`, `FINANCE_CONTROLLER` | Enum | No | Role of authorizer. |
| `approver_id` | VARCHAR(32) | Yes | User identity | Code | No | Approver identity. |
| `decision` | VARCHAR(16) | Yes | `APPROVED`, `REJECTED`, `REVISION_REQUESTED` | Enum | No | Authoritative verdict. |
| `comments` | TEXT | No | Free-form text | Text | No | Review remarks. |
| `decided_at` | TIMESTAMP | Yes | ISO 8601 string | Time | No | Sign-off timestamp. |

---

### 4.5 PayrollExport
*The final published payroll file transmitted to banking switches.*

| Field | Type | Required | Allowed Values / Constraints | Units | Uniqueness | Description / Validation Rule |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `export_id` | VARCHAR(32) | Yes | `PEX-YYYY-<seq>` (e.g. `PEX-2026-000001`) | Code | PK | Immutable export transaction. |
| `payroll_input_id`| VARCHAR(32)| Yes | FK $\rightarrow$ `PayrollInput.payroll_input_id` | Code | Unique | 1:1 with approved input. |
| `pay_period_id`| VARCHAR(16) | Yes | FK $\rightarrow$ `PayPeriod.pay_period_id`| Code | No | Target period. |
| `employee_id` | VARCHAR(16) | Yes | FK $\rightarrow$ `Employee.employee_id` | Code | No | Recipient worker. |
| `bank_account_no`| VARCHAR(32) | Yes | Non-null valid account | Digits| No | Bank account for disbursement. |
| `approved_gross`| DECIMAL(10,2)| Yes| Matches input `gross_pay` | Currency | No | Verified gross. |
| `approved_net` | DECIMAL(10,2)| Yes | Matches input `net_pay` | Currency | No | Verified net. |
| `reconciliation_hash`| VARCHAR(64)| Yes| SHA-256 string | Hex | No | Cryptographic seal of input & approvals. |
| `export_timestamp`| TIMESTAMP | Yes | ISO 8601 string | Time | No | Transmission timestamp. |

---

## 5. Planted Anomaly Ground Truth Specification

| `issue_type` | Trigger Condition | Target Entity | Expected Validation Rule |
| :--- | :--- | :--- | :--- |
| `HOURS_EXCEED_MAXIMUM` | Total period hours $> 200.00$ or daily $> 16.00$ | `TimeEntry` / `PayrollInput` | `RULE-001` (Hours Threshold) |
| `DUPLICATE_ALLOWANCE` | Same allowance type assigned $>1$ time in same pay period | `Allowance` | `RULE-002` (Duplicate Allowance) |
| `UNAPPROVED_TIME_EXPORTED` | Attempted inclusion of `TimeEntry.status != 'APPROVED'` | `TimeEntry` / `PayrollInput` | `RULE-003` (Approval Gate) |
| `DOUBLE_LEAVE_DEDUCTION` | Single unpaid leave record debited two or more times | `Deduction` | `RULE-004` (Duplicate Deduction) |
| `RECONCILIATION_MISMATCH` | Injected variance where `gross != base + overtime + allowance` | `PayrollInput` | `RULE-005` (Arithmetic Reconciliation) |
| `MISSING_BANK_TAX` | Active employee with `NULL` or blank bank/tax ID | `Employee` / `PayrollInput` | `RULE-006` (Compliance Gate) |
