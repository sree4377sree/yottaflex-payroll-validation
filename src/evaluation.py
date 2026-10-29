"""
Evaluation & Metrics Engine.
Evaluates detection accuracy (Precision, Recall, F1) against separate Ground Truth.
"""

from typing import List, Dict, Any
from src.models import ExceptionModel

class EvaluationEngine:
    def __init__(self, ground_truth: List[Dict[str, Any]], detected_exceptions: List[ExceptionModel]):
        self.ground_truth = ground_truth
        self.detected_exceptions = detected_exceptions

    def compute_metrics(self) -> Dict[str, Any]:
        """Calculates Precision, Recall, F1, and breakdown per issue type."""
        gt_by_issue: Dict[str, List[Dict[str, Any]]] = {}
        for gt in self.ground_truth:
            gt_by_issue.setdefault(gt["issue_type"], []).append(gt)

        det_by_issue: Dict[str, List[ExceptionModel]] = {}
        for ex in self.detected_exceptions:
            det_by_issue.setdefault(ex.issue_type, []).append(ex)

        all_issue_types = sorted(list(set(list(gt_by_issue.keys()) + list(det_by_issue.keys()))))
        
        breakdown = {}
        total_tp = 0
        total_fp = 0
        total_fn = 0

        for issue in all_issue_types:
            gts = gt_by_issue.get(issue, [])
            dets = det_by_issue.get(issue, [])

            # Expand any 'ALL' pay_period_id in ground truth to match actual periods
            gt_keys = set()
            for g in gts:
                if g["pay_period_id"] == "ALL":
                    # Matches any period for this employee where exception was raised
                    matched_periods = {d.pay_period_id for d in dets if d.employee_id == g["employee_id"]}
                    if matched_periods:
                        for p in matched_periods:
                            gt_keys.add((g["employee_id"], p))
                    else:
                        gt_keys.add((g["employee_id"], "ALL"))
                else:
                    gt_keys.add((g["employee_id"], g["pay_period_id"]))

            det_keys = {(d.employee_id, d.pay_period_id) for d in dets}

            tp = len(gt_keys.intersection(det_keys))
            fp = len(det_keys - gt_keys)
            fn = len(gt_keys - det_keys)

            precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
            recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 1.0

            breakdown[issue] = {
                "ground_truth_count": len(gts),
                "detected_count": len(dets),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4)
            }

            total_tp += tp
            total_fp += fp
            total_fn += fn

        overall_precision = (total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 1.0
        overall_recall = (total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 1.0
        overall_f1 = (2 * overall_precision * overall_recall / (overall_precision + overall_recall)) if (overall_precision + overall_recall) > 0 else 1.0

        return {
            "summary": {
                "total_planted_anomalies": len(self.ground_truth),
                "total_detected_exceptions": len(self.detected_exceptions),
                "overall_precision": round(overall_precision, 4),
                "overall_recall": round(overall_recall, 4),
                "overall_f1_score": round(overall_f1, 4)
            },
            "issue_breakdown": breakdown
        }
