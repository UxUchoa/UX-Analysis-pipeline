#!/usr/bin/env python3
"""
Advanced insights and anomaly detection engine for UX data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class AnomalyFinding:
    """Represents one detected anomaly."""

    type: str
    description: str
    affected_rows: List[int]
    severity: str
    metric: str


class UXInsightsEngine:
    """Extract metrics, outliers, and actionable recommendations from UX datasets."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
        self.anomalies: List[AnomalyFinding] = []

    def detect_outliers_iqr(self, column: str, multiplier: float = 1.5) -> List[int]:
        if column not in self.numeric_cols:
            return []

        q1 = self.df[column].quantile(0.25)
        q3 = self.df[column].quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        outlier_indices = self.df[
            (self.df[column] < lower_bound) | (self.df[column] > upper_bound)
        ].index.tolist()
        return outlier_indices

    def detect_statistical_outliers(self, column: str, std_dev: float = 3.0) -> List[int]:
        if column not in self.numeric_cols:
            return []

        mean = self.df[column].mean()
        std = self.df[column].std()
        if std == 0:
            return []

        z_scores = np.abs((self.df[column] - mean) / std)
        outlier_indices = self.df[z_scores > std_dev].index.tolist()
        return outlier_indices

    def detect_inconsistencies(self) -> List[AnomalyFinding]:
        findings: List[AnomalyFinding] = []

        success_col = None
        satisfaction_col = None
        for col in self.df.columns:
            lower_col = col.lower()
            if "success" in lower_col:
                success_col = col
            if "satisfaction" in lower_col or "rating" in lower_col:
                satisfaction_col = col

        if success_col and satisfaction_col:
            mismatches = self.df[(self.df[success_col] == True) & (self.df[satisfaction_col] < 3)]
            if len(mismatches) > 0:
                findings.append(
                    AnomalyFinding(
                        type="Inconsistency",
                        description=(
                            f"Found {len(mismatches)} cases where task succeeded but "
                            "satisfaction is low (< 3)."
                        ),
                        affected_rows=mismatches.index.tolist(),
                        severity="High",
                        metric=f"{success_col} vs {satisfaction_col}",
                    )
                )

        time_col = None
        error_col = None
        for col in self.df.columns:
            lower_col = col.lower()
            if "time" in lower_col or "duration" in lower_col:
                time_col = col
            if "error" in lower_col:
                error_col = col

        if time_col and error_col:
            time_threshold = self.df[time_col].quantile(0.75)
            hesitant_users = self.df[(self.df[time_col] > time_threshold) & (self.df[error_col] == 0)]
            if len(hesitant_users) > 0:
                findings.append(
                    AnomalyFinding(
                        type="Pattern",
                        description=(
                            f"Found {len(hesitant_users)} users taking longer but making no errors. "
                            "Possible hesitation/confusion."
                        ),
                        affected_rows=hesitant_users.index.tolist(),
                        severity="Medium",
                        metric=f"{time_col} vs {error_col}",
                    )
                )

        return findings

    def detect_all_anomalies(self) -> List[AnomalyFinding]:
        all_findings: List[AnomalyFinding] = []

        for col in self.numeric_cols:
            outliers_iqr = self.detect_outliers_iqr(col)
            if len(outliers_iqr) > 0:
                all_findings.append(
                    AnomalyFinding(
                        type="Outlier",
                        description=f"Found {len(outliers_iqr)} outliers in '{col}' using IQR",
                        affected_rows=outliers_iqr,
                        severity="Medium",
                        metric=col,
                    )
                )

        all_findings.extend(self.detect_inconsistencies())

        missing_by_col = self.df.isnull().sum()
        for col, count in missing_by_col[missing_by_col > 0].items():
            ratio = count / len(self.df)
            all_findings.append(
                AnomalyFinding(
                    type="Missing Data",
                    description=f"Column '{col}' has {count} missing values ({ratio * 100:.1f}%)",
                    affected_rows=self.df[self.df[col].isnull()].index.tolist(),
                    severity="Low" if ratio < 0.1 else "Medium",
                    metric=col,
                )
            )

        self.anomalies = all_findings
        return all_findings

    def extract_key_metrics(self) -> Dict[str, float]:
        metrics: Dict[str, float] = {}

        for col in self.df.columns:
            if "success" in col.lower():
                metrics["success_rate"] = float((self.df[col] == True).sum() / len(self.df) * 100)
                break

        for col in self.df.columns:
            if "time" in col.lower() or "duration" in col.lower():
                metrics["avg_completion_time"] = float(self.df[col].mean())
                break

        for col in self.df.columns:
            if "error" in col.lower():
                metrics["avg_error_count"] = float(self.df[col].mean())
                break

        for col in self.df.columns:
            if "satisfaction" in col.lower() or "rating" in col.lower():
                metrics["avg_satisfaction"] = float(self.df[col].mean())
                break

        return metrics

    def generate_insights_text(self) -> List[str]:
        insights: List[str] = []
        metrics = self.extract_key_metrics()

        if "success_rate" in metrics:
            sr = metrics["success_rate"]
            if sr >= 90:
                insights.append(f"Excellent task success rate ({sr:.1f}%).")
            elif sr >= 70:
                insights.append(f"Good task success rate ({sr:.1f}%), with room for improvement.")
            elif sr >= 50:
                insights.append(f"Moderate task success rate ({sr:.1f}), indicating usability friction.")
            else:
                insights.append(f"Low task success rate ({sr:.1f}), indicating critical usability issues.")

        if "avg_completion_time" in metrics:
            ct = metrics["avg_completion_time"]
            speed = "efficient" if ct < 60 else "reasonable" if ct < 180 else "slow"
            insights.append(f"Average completion time is {ct:.0f}s, which is {speed}.")

        if "avg_error_count" in metrics:
            ec = metrics["avg_error_count"]
            if ec == 0:
                insights.append("Average error count is zero.")
            elif ec < 1:
                insights.append(f"Average error count is low ({ec:.1f}).")
            else:
                insights.append(f"Average error count is elevated ({ec:.1f}).")

        if "avg_satisfaction" in metrics:
            sat = metrics["avg_satisfaction"]
            if sat >= 4.5:
                insights.append(f"Very high user satisfaction ({sat:.1f}/5).")
            elif sat >= 3.5:
                insights.append(f"Good user satisfaction ({sat:.1f}/5).")
            elif sat >= 2.5:
                insights.append(f"Moderate user satisfaction ({sat:.1f}/5).")
            else:
                insights.append(f"Low user satisfaction ({sat:.1f}/5).")

        return insights

    def get_recommendations(self) -> List[str]:
        recommendations: List[str] = []
        anomalies = self.anomalies if self.anomalies else self.detect_all_anomalies()
        metrics = self.extract_key_metrics()

        for anomaly in anomalies:
            if anomaly.type == "Inconsistency" and "success" in anomaly.metric.lower():
                recommendations.append(
                    "Review successful tasks with low satisfaction to find hidden friction points."
                )
            if anomaly.type == "Pattern" and "longer" in anomaly.description.lower():
                recommendations.append(
                    "Interview users with long completion time and zero errors to identify hesitation causes."
                )

        if metrics.get("success_rate", 100) < 80:
            recommendations.append("Run focused usability tests on failed task paths.")
        if metrics.get("avg_error_count", 0) > 1:
            recommendations.append("Simplify UI flows and improve affordances to reduce errors.")
        if metrics.get("avg_satisfaction", 5) < 3.5:
            recommendations.append("Prioritize redesign of top pain points captured in sessions.")

        return recommendations


def analyze_excel_data(df: pd.DataFrame) -> Dict:
    engine = UXInsightsEngine(df)
    results = {
        "metrics": engine.extract_key_metrics(),
        "insights": engine.generate_insights_text(),
        "anomalies": engine.detect_all_anomalies(),
        "recommendations": engine.get_recommendations(),
        "data_shape": {"rows": len(df), "columns": len(df.columns)},
        "data_types": df.dtypes.to_dict(),
        "missing_data": df.isnull().sum().to_dict(),
    }
    return results


if __name__ == "__main__":
    data = {
        "Session_ID": [f"S{i:03d}" for i in range(1, 21)],
        "Task_Name": ["Login"] * 10 + ["Checkout"] * 10,
        "Success": [
            True,
            True,
            False,
            True,
            True,
            True,
            False,
            True,
            True,
            True,
            True,
            False,
            False,
            True,
            False,
            True,
            True,
            False,
            True,
            True,
        ],
        "Completion_Time": [
            45,
            50,
            120,
            40,
            55,
            48,
            180,
            42,
            51,
            47,
            180,
            350,
            420,
            195,
            380,
            170,
            210,
            400,
            185,
            190,
        ],
        "Error_Count": [0, 0, 2, 0, 1, 0, 3, 0, 0, 0, 1, 4, 5, 1, 4, 0, 2, 3, 1, 0],
        "Satisfaction": [5, 4, 2, 5, 4, 5, 1, 5, 4, 5, 4, 1, 1, 3, 2, 4, 3, 1, 4, 4],
    }
    sample_df = pd.DataFrame(data)
    out = analyze_excel_data(sample_df)
    print("Metrics:", out["metrics"])
    print("Insights:")
    for item in out["insights"]:
        print("-", item)
    print("Anomalies:", len(out["anomalies"]))
