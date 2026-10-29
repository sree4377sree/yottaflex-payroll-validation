"""
Step 10 Verification: Deterministic Reproducibility Test.
Regenerates twice with the same seed and asserts exact row count and hash equality.
"""

import hashlib
import json
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.generator import SyntheticDataGenerator
from src.validator import ValidationEngine

class TestReproducibility(unittest.TestCase):
    def test_exact_reproducibility(self):
        seed = 20261022
        scale = "starter"

        # Run 1
        gen1 = SyntheticDataGenerator(seed=seed, scale=scale)
        data1 = gen1.generate_all()
        val1 = ValidationEngine(data1)
        exc1 = val1.run_all_validations()

        # Run 2
        gen2 = SyntheticDataGenerator(seed=seed, scale=scale)
        data2 = gen2.generate_all()
        val2 = ValidationEngine(data2)
        exc2 = val2.run_all_validations()

        # 1. Compare row counts
        self.assertEqual(len(data1["employees"]), len(data2["employees"]))
        self.assertEqual(len(data1["time_entries"]), len(data2["time_entries"]))
        self.assertEqual(len(data1["leave_records"]), len(data2["leave_records"]))
        self.assertEqual(len(data1["allowances"]), len(data2["allowances"]))
        self.assertEqual(len(data1["deductions"]), len(data2["deductions"]))
        self.assertEqual(len(data1["payroll_inputs"]), len(data2["payroll_inputs"]))
        self.assertEqual(len(exc1), len(exc2))

        # 2. Compare data checksums
        def compute_checksum(dataset):
            raw = json.dumps([
                {
                    "pin": p.payroll_input_id,
                    "gross": p.gross_pay,
                    "net": p.net_pay,
                    "variance": p.reconciliation_variance
                }
                for p in dataset["payroll_inputs"]
            ], sort_keys=True)
            return hashlib.sha256(raw.encode("utf-8")).hexdigest()

        hash1 = compute_checksum(data1)
        hash2 = compute_checksum(data2)

        self.assertEqual(hash1, hash2, "Checksums between identical seed runs must match exactly!")
        print(f"\n[PASS] Step 10 Verification: Run 1 Hash ({hash1[:16]}...) == Run 2 Hash ({hash2[:16]}...)")

if __name__ == "__main__":
    unittest.main()
