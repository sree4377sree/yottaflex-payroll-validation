"""
Payroll Exporter & Approval Gateway.
Ensures ONLY approved, reconciled records are exported while preserving audit traceability.
"""

import hashlib
import sqlite3
import csv
import json
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone

from src.models import (
    PayrollInputModel, ApprovalModel, PayrollExportModel, EmployeeModel,
    ExceptionModel
)

class PayrollExporter:
    def __init__(self, data: Dict[str, Any], exceptions: List[ExceptionModel]):
        self.payroll_inputs: List[PayrollInputModel] = data["payroll_inputs"]
        self.employees: List[EmployeeModel] = data["employees"]
        self.exceptions: List[ExceptionModel] = exceptions
        
        self.approvals: List[ApprovalModel] = []
        self.exports: List[PayrollExportModel] = []
        
        self.emp_map = {e.employee_id: e for e in self.employees}

    def process_approvals_and_export(self) -> Tuple[List[ApprovalModel], List[PayrollExportModel]]:
        """
        Processes sign-offs for clean inputs, creates cryptographic hashes,
        and produces the immutable payroll export.
        """
        self.approvals = []
        self.exports = []
        export_seq = 0
        now_ts = datetime.now(timezone.utc).isoformat()

        for pin in self.payroll_inputs:
            # Rejection Gate: FLAGGED records cannot be approved or exported
            if pin.status == "FLAGGED":
                self.approvals.append(ApprovalModel(
                    approval_id=f"APP-REJ-{pin.payroll_input_id}",
                    payroll_input_id=pin.payroll_input_id,
                    approver_role="FINANCE_CONTROLLER",
                    approver_id="SYSTEM_VALIDATOR",
                    decision="REJECTED",
                    comments="Blocked at pre-export validation gate due to active exceptions.",
                    decided_at=now_ts
                ))
                continue

            # Record Approved
            pin.status = "APPROVED"
            app_id = f"APP-OK-{pin.payroll_input_id}"
            self.approvals.append(ApprovalModel(
                approval_id=app_id,
                payroll_input_id=pin.payroll_input_id,
                approver_role="FINANCE_CONTROLLER",
                approver_id="FIN_ADMIN_01",
                decision="APPROVED",
                comments="Pre-export validations and reconciliation checks passed.",
                decided_at=now_ts
            ))

            # Generate Payroll Export
            emp = self.emp_map.get(pin.employee_id)
            bank_acc = emp.bank_account_no if emp and emp.bank_account_no else "UNKNOWN"

            export_seq += 1
            export_id = f"PEX-2026-{export_seq:06d}"

            # Compute cryptographic audit seal (SHA-256)
            raw_seal = f"{export_id}|{pin.payroll_input_id}|{pin.employee_id}|{pin.gross_pay:.2f}|{pin.net_pay:.2f}|{now_ts}"
            reconciliation_hash = hashlib.sha256(raw_seal.encode("utf-8")).hexdigest()

            export_record = PayrollExportModel(
                export_id=export_id,
                payroll_input_id=pin.payroll_input_id,
                pay_period_id=pin.pay_period_id,
                employee_id=pin.employee_id,
                bank_account_no=bank_acc,
                approved_gross=pin.gross_pay,
                approved_net=pin.net_pay,
                reconciliation_hash=reconciliation_hash,
                export_timestamp=now_ts
            )
            self.exports.append(export_record)
            pin.status = "EXPORTED"

        return self.approvals, self.exports

    def save_to_sqlite(self, db_path: str, data: Dict[str, Any]):
        """Persists all 12 entities and exceptions into SQLite database."""
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Execute DDL
        schema_path = os.path.join(os.path.dirname(__file__), "..", "schema", "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            cur.executescript(f.read())

        # Bulk inserts
        cur.executemany(
            "INSERT OR REPLACE INTO pay_groups VALUES (?, ?, ?, ?, ?, ?)",
            [(pg.pay_group_id, pg.name, pg.frequency, pg.standard_hours, pg.max_overtime_hours, 1 if pg.is_active else 0) for pg in data["pay_groups"]]
        )

        cur.executemany(
            "INSERT OR REPLACE INTO pay_periods VALUES (?, ?, ?, ?, ?, ?)",
            [(pp.pay_period_id, pp.pay_group_id, pp.start_date, pp.end_date, pp.cut_off_date, pp.status) for pp in data["pay_periods"]]
        )

        cur.executemany(
            "INSERT OR REPLACE INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(e.employee_id, e.pay_group_id, e.first_name, e.last_name, e.email, e.bank_account_no, e.bank_ifsc, e.tax_identifier, e.hourly_rate, e.status, e.created_at) for e in data["employees"]]
        )

        cur.executemany(
            "INSERT OR REPLACE INTO time_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(t.time_entry_id, t.employee_id, t.pay_period_id, t.work_date, t.regular_hours, t.overtime_hours, t.status, t.version, t.created_at) for t in data["time_entries"]]
        )

        cur.executemany(
            "INSERT OR REPLACE INTO leave_records VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(l.leave_record_id, l.employee_id, l.pay_period_id, l.leave_date, l.leave_type, l.hours_deducted, l.status) for l in data["leave_records"]]
        )

        cur.executemany(
            "INSERT OR REPLACE INTO allowances VALUES (?, ?, ?, ?, ?, ?)",
            [(a.allowance_id, a.employee_id, a.pay_period_id, a.allowance_type, a.amount, 1 if a.is_taxable else 0) for a in data["allowances"]]
        )

        cur.executemany(
            "INSERT OR REPLACE INTO deductions VALUES (?, ?, ?, ?, ?, ?)",
            [(d.deduction_id, d.employee_id, d.pay_period_id, d.deduction_type, d.amount, d.source_ref_id) for d in data["deductions"]]
        )

        cur.executemany(
            "INSERT OR REPLACE INTO payroll_inputs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(p.payroll_input_id, p.employee_id, p.pay_period_id, p.regular_hours, p.overtime_hours, p.base_earnings, p.overtime_earnings, p.total_allowance, p.total_deduction, p.gross_pay, p.net_pay, p.reconciliation_variance, p.status, p.aggregated_at) for p in data["payroll_inputs"]]
        )

        cur.executemany(
            "INSERT OR REPLACE INTO exceptions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(ex.exception_id, ex.rule_id, ex.entity_type, ex.entity_id, ex.employee_id, ex.pay_period_id, ex.issue_type, ex.status, ex.details, ex.created_at) for ex in self.exceptions]
        )

        cur.executemany(
            "INSERT OR REPLACE INTO approvals VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(ap.approval_id, ap.payroll_input_id, ap.approver_role, ap.approver_id, ap.decision, ap.comments, ap.decided_at) for ap in self.approvals]
        )

        cur.executemany(
            "INSERT OR REPLACE INTO payroll_exports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(px.export_id, px.payroll_input_id, px.pay_period_id, px.employee_id, px.bank_account_no, px.approved_gross, px.approved_net, px.reconciliation_hash, px.export_timestamp) for px in self.exports]
        )

        conn.commit()
        conn.close()

    def export_csv_and_json(self, output_dir: str, data: Dict[str, Any]):
        """Exports data dictionary tables into standalone CSVs and JSON."""
        os.makedirs(output_dir, exist_ok=True)

        # 1. Export Payroll Exports (Final Bank File)
        csv_path = os.path.join(output_dir, "payroll_exports.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["export_id", "payroll_input_id", "pay_period_id", "employee_id", "bank_account_no", "approved_gross", "approved_net", "reconciliation_hash", "export_timestamp"])
            for px in self.exports:
                writer.writerow([px.export_id, px.payroll_input_id, px.pay_period_id, px.employee_id, px.bank_account_no, f"{px.approved_gross:.2f}", f"{px.approved_net:.2f}", px.reconciliation_hash, px.export_timestamp])

        # 2. Export Exceptions Log
        exc_path = os.path.join(output_dir, "exceptions.csv")
        with open(exc_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["exception_id", "rule_id", "entity_type", "entity_id", "employee_id", "pay_period_id", "issue_type", "status", "details", "created_at"])
            for ex in self.exceptions:
                writer.writerow([ex.exception_id, ex.rule_id, ex.entity_type, ex.entity_id, ex.employee_id, ex.pay_period_id, ex.issue_type, ex.status, ex.details, ex.created_at])

        # 3. Export Ground Truth
        gt_path = os.path.join(output_dir, "ground_truth.csv")
        gt_list = data.get("ground_truth", [])
        with open(gt_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["anomaly_id", "employee_id", "pay_period_id", "issue_type", "target_entity", "target_id", "expected_rule", "description"])
            for gt in gt_list:
                writer.writerow([gt["anomaly_id"], gt["employee_id"], gt["pay_period_id"], gt["issue_type"], gt["target_entity"], gt["target_id"], gt["expected_rule"], gt["description"]])

        # 4. Export Ground Truth JSON
        gt_json_path = os.path.join(output_dir, "ground_truth.json")
        with open(gt_json_path, "w", encoding="utf-8") as f:
            json.dump(gt_list, f, indent=2)
