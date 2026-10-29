"""
Arithmetic Reconciliation & Export Integrity Tests.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.generator import SyntheticDataGenerator
from src.validator import ValidationEngine
from src.exporter import PayrollExporter

class TestReconciliation(unittest.TestCase):
    def setUp(self):
        self.generator = SyntheticDataGenerator(seed=20261022, scale="starter")
        self.data = self.generator.generate_all()
        self.validator = ValidationEngine(self.data)
        self.exceptions = self.validator.run_all_validations()
        self.exporter = PayrollExporter(self.data, self.exceptions)
        self.approvals, self.exports = self.exporter.process_approvals_and_export()

    def test_zero_reconciliation_leakage(self):
        """Ensures that NO exported record has non-zero reconciliation variance."""
        pin_map = {p.payroll_input_id: p for p in self.data["payroll_inputs"]}
        
        for exp in self.exports:
            pin = pin_map[exp.payroll_input_id]
            # Reconciliation invariance
            self.assertEqual(pin.reconciliation_variance, 0.00,
                             f"Exported record {exp.export_id} has non-zero variance!")
            self.assertEqual(pin.status, "EXPORTED")

    def test_blocked_records_not_in_exports(self):
        """Ensures that every FLAGGED/blocked record is strictly excluded from payroll exports."""
        flagged_pin_ids = {p.payroll_input_id for p in self.data["payroll_inputs"] if p.status == "FLAGGED"}
        exported_pin_ids = {exp.payroll_input_id for exp in self.exports}

        intersection = flagged_pin_ids.intersection(exported_pin_ids)
        self.assertEqual(len(intersection), 0,
                         f"Flagged records leaked into export file: {intersection}")

    def test_cryptographic_hash_integrity(self):
        """Verifies that all exported records carry a valid 64-character SHA-256 seal."""
        for exp in self.exports:
            self.assertEqual(len(exp.reconciliation_hash), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in exp.reconciliation_hash))

if __name__ == "__main__":
    unittest.main()
