"""
Synthetic Data Generator with Parameterized Volume, Deterministic Seeding,
and Labelled Ground-Truth Anomaly Injection.
"""

import random
import calendar
from datetime import date, timedelta
from typing import Dict, List, Tuple, Any

from src.config import (
    DEFAULT_SEED, SCALES, PAY_GROUPS, ALLOWANCE_TYPES, DEDUCTION_TYPES,
    ISSUE_HOURS_EXCEED_MAX, ISSUE_DUPLICATE_ALLOWANCE, ISSUE_UNAPPROVED_TIME,
    ISSUE_DOUBLE_LEAVE_DEDUCTION, ISSUE_RECONCILIATION_MISMATCH, ISSUE_MISSING_BANK_TAX
)
from src.models import (
    PayGroupModel, PayPeriodModel, EmployeeModel, TimeEntryModel,
    LeaveRecordModel, AllowanceModel, DeductionModel, PayrollInputModel
)

FIRST_NAMES = [
    "Aarav", "Aditi", "Rohan", "Priya", "Rahul", "Sneha", "Vikram", "Ananya",
    "Karthik", "Pooja", "Arjun", "Divya", "Suresh", "Meera", "Nikhil", "Deepa",
    "Amit", "Sunita", "Rajesh", "Kavita", "Sanjay", "Neha", "Manoj", "Shweta",
    "Vijay", "Ritu", "Alok", "Preeti", "Gaurav", "Nisha", "Harish", "Asha"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Iyer", "Nair", "Rao", "Gupta",
    "Singh", "Kumar", "Chopra", "Mehta", "Joshi", "Bhat", "Deshmukh", "Pillai",
    "Menon", "Mukherjee", "Das", "Banerjee", "Kulkarni", "Shenoy", "Hegde", "Mishra"
]

class SyntheticDataGenerator:
    def __init__(self, seed: int = DEFAULT_SEED, scale: str = "starter"):
        self.seed = seed
        self.scale_name = scale
        self.config = SCALES.get(scale, SCALES["starter"])
        self.rng = random.Random(self.seed)
        
        # Generated collections
        self.pay_groups: List[PayGroupModel] = []
        self.pay_periods: List[PayPeriodModel] = []
        self.employees: List[EmployeeModel] = []
        self.time_entries: List[TimeEntryModel] = []
        self.leave_records: List[LeaveRecordModel] = []
        self.allowances: List[AllowanceModel] = []
        self.deductions: List[DeductionModel] = []
        self.payroll_inputs: List[PayrollInputModel] = []
        
        # Ground truth labels for injected anomalies (never leaked into inputs)
        self.ground_truth: List[Dict[str, Any]] = []

    def generate_all(self) -> Dict[str, Any]:
        """Executes the full generation pipeline in strict dependency order."""
        self._generate_master_pay_groups()
        self._generate_master_pay_periods()
        self._generate_master_employees()
        self._generate_transactions_and_anomalies()
        self._aggregate_payroll_inputs()
        
        return {
            "pay_groups": self.pay_groups,
            "pay_periods": self.pay_periods,
            "employees": self.employees,
            "time_entries": self.time_entries,
            "leave_records": self.leave_records,
            "allowances": self.allowances,
            "deductions": self.deductions,
            "payroll_inputs": self.payroll_inputs,
            "ground_truth": self.ground_truth
        }

    def _generate_master_pay_groups(self):
        self.pay_groups = [
            PayGroupModel(
                pay_group_id=pg["id"],
                name=pg["name"],
                frequency=pg["frequency"],
                standard_hours=pg["standard_hours"],
                max_overtime_hours=pg["max_overtime_hours"],
                is_active=True
            )
            for pg in PAY_GROUPS
        ]

    def _generate_master_pay_periods(self):
        year = self.config["year"]
        num_months = self.config["num_months"]
        self.pay_periods = []
        
        for m in range(1, num_months + 1):
            period_id = f"PP-{year}-{m:02d}"
            _, last_day = calendar.monthrange(year, m)
            start_date = f"{year}-{m:02d}-01"
            end_date = f"{year}-{m:02d}-{last_day:02d}"
            cut_off_date = f"{year}-{m:02d}-{last_day:02d}"
            
            # Default to primary pay group PG-TECH, also accessible to other groups
            self.pay_periods.append(PayPeriodModel(
                pay_period_id=period_id,
                pay_group_id="PG-TECH",
                start_date=start_date,
                end_date=end_date,
                cut_off_date=cut_off_date,
                status="PROCESSING"
            ))

    def _generate_master_employees(self):
        num_employees = self.config["num_employees"]
        anomaly_rate = self.config["anomaly_rate"]
        self.employees = []
        
        for i in range(1, num_employees + 1):
            emp_id = f"EMP-{i:06d}"
            first = self.rng.choice(FIRST_NAMES)
            last = self.rng.choice(LAST_NAMES)
            email = f"{first.lower()}.{last.lower()}.{i}@yottaflex-corp.com"
            pg = self.rng.choice(self.pay_groups).pay_group_id
            
            # Base rates: Junior (300-500), Mid (600-1000), Senior/Exec (1200-2500)
            tier = self.rng.choices(["JUNIOR", "MID", "SENIOR"], weights=[0.5, 0.35, 0.15])[0]
            if tier == "JUNIOR":
                hourly_rate = round(self.rng.uniform(350.0, 550.0), 2)
            elif tier == "MID":
                hourly_rate = round(self.rng.uniform(650.0, 1100.0), 2)
            else:
                hourly_rate = round(self.rng.uniform(1400.0, 2600.0), 2)

            # Plant anomaly: Missing bank or tax identification
            has_missing_compliance = (self.rng.random() < (anomaly_rate * 0.25))
            if has_missing_compliance:
                bank_acc = None
                ifsc = None
                tax_id = None
                self.ground_truth.append({
                    "anomaly_id": f"GT-COMPLIANCE-{emp_id}",
                    "employee_id": emp_id,
                    "pay_period_id": "ALL",
                    "issue_type": ISSUE_MISSING_BANK_TAX,
                    "target_entity": "Employee",
                    "target_id": emp_id,
                    "expected_rule": "RULE-006",
                    "description": f"Employee {emp_id} lacks bank account and tax identification."
                })
            else:
                bank_acc = f"9100{self.rng.randint(10000000, 99999999)}"
                ifsc = f"HDFC000{self.rng.randint(1000, 9999)}"
                tax_id = f"ABCDE{self.rng.randint(1000, 9999)}F"

            self.employees.append(EmployeeModel(
                employee_id=emp_id,
                pay_group_id=pg,
                first_name=first,
                last_name=last,
                email=email,
                hourly_rate=hourly_rate,
                bank_account_no=bank_acc,
                bank_ifsc=ifsc,
                tax_identifier=tax_id,
                status="ACTIVE",
                created_at="2026-01-01T09:00:00"
            ))

    def _generate_transactions_and_anomalies(self):
        year = self.config["year"]
        anomaly_rate = self.config["anomaly_rate"]
        
        self.time_entries = []
        self.leave_records = []
        self.allowances = []
        self.deductions = []

        for period in self.pay_periods:
            p_month = int(period.pay_period_id.split("-")[2])
            num_days = calendar.monthrange(year, p_month)[1]
            
            # Business working days (exclude Saturday=5, Sunday=6)
            work_days = [
                date(year, p_month, d) for d in range(1, num_days + 1)
                if date(year, p_month, d).weekday() < 5
            ]

            for emp in self.employees:
                emp_id = emp.employee_id
                
                # Check for Planted Anomaly: Hours Exceed Maximum
                inject_hours_exceed = (self.rng.random() < (anomaly_rate * 0.25))
                # Check for Planted Anomaly: Unapproved Time Exported
                inject_unapproved_time = (self.rng.random() < (anomaly_rate * 0.20))
                # Check for Planted Anomaly: Duplicate Allowance
                inject_duplicate_allowance = (self.rng.random() < (anomaly_rate * 0.20))
                # Check for Planted Anomaly: Double Leave Deduction
                inject_double_leave = (self.rng.random() < (anomaly_rate * 0.20))
                
                # 1. Generate Leave Records (1-2 days leave for ~15% of employees)
                emp_leave_days = set()
                if self.rng.random() < 0.15:
                    leave_day = self.rng.choice(work_days)
                    emp_leave_days.add(leave_day)
                    l_type = "UNPAID_LOP" if (inject_double_leave or self.rng.random() < 0.3) else "PAID_CASUAL"
                    leave_id = f"LEV-{emp_id}-{leave_day.isoformat()}"
                    
                    self.leave_records.append(LeaveRecordModel(
                        leave_record_id=leave_id,
                        employee_id=emp_id,
                        pay_period_id=period.pay_period_id,
                        leave_date=leave_day.isoformat(),
                        leave_type=l_type,
                        hours_deducted=8.0,
                        status="APPROVED"
                    ))
                    
                    # If unpaid leave, create corresponding deduction
                    if l_type == "UNPAID_LOP":
                        ded_amount = round(8.0 * emp.hourly_rate, 2)
                        ded_id = f"DED-{emp_id}-{period.pay_period_id}-01"
                        self.deductions.append(DeductionModel(
                            deduction_id=ded_id,
                            employee_id=emp_id,
                            pay_period_id=period.pay_period_id,
                            deduction_type="UNPAID_LEAVE",
                            amount=ded_amount,
                            source_ref_id=leave_id
                        ))
                        
                        # Anomaly: Double Leave Deduction
                        if inject_double_leave:
                            dup_ded_id = f"DED-{emp_id}-{period.pay_period_id}-02"
                            self.deductions.append(DeductionModel(
                                deduction_id=dup_ded_id,
                                employee_id=emp_id,
                                pay_period_id=period.pay_period_id,
                                deduction_type="UNPAID_LEAVE",
                                amount=ded_amount,
                                source_ref_id=leave_id
                            ))
                            self.ground_truth.append({
                                "anomaly_id": f"GT-LEAVE-{dup_ded_id}",
                                "employee_id": emp_id,
                                "pay_period_id": period.pay_period_id,
                                "issue_type": ISSUE_DOUBLE_LEAVE_DEDUCTION,
                                "target_entity": "Deduction",
                                "target_id": dup_ded_id,
                                "expected_rule": "RULE-004",
                                "description": f"Unpaid leave {leave_id} debited twice in period {period.pay_period_id}."
                            })

                # 2. Generate Daily Time Entries
                total_hours_for_emp = 0.0
                for d in work_days:
                    if d in emp_leave_days:
                        continue # On leave, no regular work entry
                    
                    time_id = f"TIME-{emp_id}-{d.isoformat()}"
                    
                    if inject_hours_exceed:
                        # Planted hours exceeding policy (>16h day or >200h month)
                        reg_hours = 12.0
                        ot_hours = 6.0
                    else:
                        reg_hours = 8.0
                        ot_hours = round(self.rng.uniform(0.0, 2.0), 2) if self.rng.random() < 0.25 else 0.0
                    
                    total_hours_for_emp += (reg_hours + ot_hours)
                    
                    # Status logic
                    if inject_unapproved_time and len(self.time_entries) % 20 == 0:
                        t_status = "SUBMITTED" # Unapproved!
                        self.ground_truth.append({
                            "anomaly_id": f"GT-UNAPPROVED-{time_id}",
                            "employee_id": emp_id,
                            "pay_period_id": period.pay_period_id,
                            "issue_type": ISSUE_UNAPPROVED_TIME,
                            "target_entity": "TimeEntry",
                            "target_id": time_id,
                            "expected_rule": "RULE-003",
                            "description": f"TimeEntry {time_id} has status SUBMITTED (unapproved)."
                        })
                    else:
                        t_status = "APPROVED"

                    self.time_entries.append(TimeEntryModel(
                        time_entry_id=time_id,
                        employee_id=emp_id,
                        pay_period_id=period.pay_period_id,
                        work_date=d.isoformat(),
                        regular_hours=reg_hours,
                        overtime_hours=ot_hours,
                        status=t_status,
                        version=1,
                        created_at=f"{d.isoformat()}T18:00:00"
                    ))

                if inject_hours_exceed and total_hours_for_emp > 200.0:
                    self.ground_truth.append({
                        "anomaly_id": f"GT-OVERTIME-{emp_id}-{period.pay_period_id}",
                        "employee_id": emp_id,
                        "pay_period_id": period.pay_period_id,
                        "issue_type": ISSUE_HOURS_EXCEED_MAX,
                        "target_entity": "PayrollInput",
                        "target_id": f"PIN-{emp_id}-{period.pay_period_id}",
                        "expected_rule": "RULE-001",
                        "description": f"Total period hours ({total_hours_for_emp:.1f}h) exceeds maximum allowed threshold of 200.0h."
                    })

                # 3. Standard Allowances
                alw_id1 = f"ALW-{emp_id}-{period.pay_period_id}-01"
                self.allowances.append(AllowanceModel(
                    allowance_id=alw_id1,
                    employee_id=emp_id,
                    pay_period_id=period.pay_period_id,
                    allowance_type="HOUSING",
                    amount=8000.00,
                    is_taxable=True
                ))
                
                # Anomaly: Duplicate Allowance
                if inject_duplicate_allowance:
                    alw_id2 = f"ALW-{emp_id}-{period.pay_period_id}-02"
                    self.allowances.append(AllowanceModel(
                        allowance_id=alw_id2,
                        employee_id=emp_id,
                        pay_period_id=period.pay_period_id,
                        allowance_type="HOUSING",
                        amount=8000.00,
                        is_taxable=True
                    ))
                    self.ground_truth.append({
                        "anomaly_id": f"GT-DUPALW-{alw_id2}",
                        "employee_id": emp_id,
                        "pay_period_id": period.pay_period_id,
                        "issue_type": ISSUE_DUPLICATE_ALLOWANCE,
                        "target_entity": "Allowance",
                        "target_id": alw_id2,
                        "expected_rule": "RULE-002",
                        "description": f"Duplicate HOUSING allowance detected for {emp_id} in period {period.pay_period_id}."
                    })

                # 4. Standard Statutory Deductions (Provident Fund)
                pf_ded_id = f"DED-{emp_id}-{period.pay_period_id}-PF"
                self.deductions.append(DeductionModel(
                    deduction_id=pf_ded_id,
                    employee_id=emp_id,
                    pay_period_id=period.pay_period_id,
                    deduction_type="PROVIDENT_FUND",
                    amount=1800.00,
                    source_ref_id="STATUTORY_PF_ACT"
                ))

    def _aggregate_payroll_inputs(self):
        """
        Step 6: Calculate derived values from source records.
        Also injects deliberate reconciliation mismatch anomaly for testing.
        """
        anomaly_rate = self.config["anomaly_rate"]
        self.payroll_inputs = []

        # Index source transactions by (employee_id, pay_period_id)
        time_by_emp_period: Dict[Tuple[str, str], List[TimeEntryModel]] = {}
        for t in self.time_entries:
            key = (t.employee_id, t.pay_period_id)
            time_by_emp_period.setdefault(key, []).append(t)

        alw_by_emp_period: Dict[Tuple[str, str], List[AllowanceModel]] = {}
        for a in self.allowances:
            key = (a.employee_id, a.pay_period_id)
            alw_by_emp_period.setdefault(key, []).append(a)

        ded_by_emp_period: Dict[Tuple[str, str], List[DeductionModel]] = {}
        for d in self.deductions:
            key = (d.employee_id, d.pay_period_id)
            ded_by_emp_period.setdefault(key, []).append(d)

        emp_map = {e.employee_id: e for e in self.employees}

        for period in self.pay_periods:
            p_id = period.pay_period_id

            for emp in self.employees:
                emp_id = emp.employee_id
                key = (emp_id, p_id)
                pin_id = f"PIN-{emp_id}-{p_id}"

                emp_times = time_by_emp_period.get(key, [])
                emp_alws = alw_by_emp_period.get(key, [])
                emp_deds = ded_by_emp_period.get(key, [])

                # Aggregations
                reg_hours = sum(t.regular_hours for t in emp_times if t.status == "APPROVED")
                ot_hours = sum(t.overtime_hours for t in emp_times if t.status == "APPROVED")
                
                base_earnings = round(reg_hours * emp.hourly_rate, 2)
                ot_earnings = round(ot_hours * emp.hourly_rate * 1.5, 2)
                tot_alw = round(sum(a.amount for a in emp_alws), 2)
                tot_ded = round(sum(d.amount for d in emp_deds), 2)

                true_gross = round(base_earnings + ot_earnings + tot_alw, 2)

                # Anomaly: Planted Reconciliation Mismatch
                inject_recon_mismatch = (self.rng.random() < (anomaly_rate * 0.20))
                if inject_recon_mismatch:
                    corrupted_gross = round(true_gross + self.rng.choice([1500.0, -2500.0, 5000.0]), 2)
                    gross_pay = corrupted_gross
                    variance = round(corrupted_gross - true_gross, 2)
                    self.ground_truth.append({
                        "anomaly_id": f"GT-RECON-{pin_id}",
                        "employee_id": emp_id,
                        "pay_period_id": p_id,
                        "issue_type": ISSUE_RECONCILIATION_MISMATCH,
                        "target_entity": "PayrollInput",
                        "target_id": pin_id,
                        "expected_rule": "RULE-005",
                        "description": f"PayrollInput {pin_id} gross {gross_pay} fails reconciliation by variance of {variance}."
                    })
                else:
                    gross_pay = true_gross
                    variance = 0.00

                net_pay = round(gross_pay - tot_ded, 2)

                self.payroll_inputs.append(PayrollInputModel(
                    payroll_input_id=pin_id,
                    employee_id=emp_id,
                    pay_period_id=p_id,
                    regular_hours=round(reg_hours, 2),
                    overtime_hours=round(ot_hours, 2),
                    base_earnings=base_earnings,
                    overtime_earnings=ot_earnings,
                    total_allowance=tot_alw,
                    total_deduction=tot_ded,
                    gross_pay=gross_pay,
                    net_pay=net_pay,
                    reconciliation_variance=variance,
                    status="DRAFT",
                    aggregated_at=f"{period.end_date}T23:59:59"
                ))
