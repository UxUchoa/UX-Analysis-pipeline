#!/usr/bin/env python3
"""Create sample Excel file for testing."""

from pathlib import Path

import numpy as np
import pandas as pd

np.random.seed(42)

data = {
    "Session_ID": [f"S{i:04d}" for i in range(1, 51)],
    "Task_Name": ["Login"] * 25 + ["Checkout"] * 25,
    "Success": np.random.choice([True, False], 50, p=[0.72, 0.28]),
    "Completion_Time_Sec": np.random.normal(150, 80, 50).astype(int),
    "Error_Count": np.random.poisson(1.2, 50),
    "Satisfaction_Rating": np.random.randint(1, 6, 50),
    "User_Age": np.random.randint(20, 70, 50),
    "Experience_Level": np.random.choice(
        ["Novice", "Intermediate", "Expert"],
        50,
        p=[0.3, 0.4, 0.3],
    ),
}

df = pd.DataFrame(data)

success_mask = df["Success"] == True
fail_mask = df["Success"] == False

error_count_dtype = df["Error_Count"].dtype
adjusted_error_count = df["Error_Count"].astype("float64").copy()
adjusted_error_count.loc[success_mask] = adjusted_error_count.loc[success_mask] * 0.3
adjusted_error_count.loc[fail_mask] = adjusted_error_count.loc[fail_mask] * 2.5
df["Error_Count"] = adjusted_error_count.astype(error_count_dtype)

df.loc[success_mask, "Satisfaction_Rating"] = np.random.randint(3, 6, success_mask.sum())
df.loc[fail_mask, "Satisfaction_Rating"] = np.random.randint(1, 4, fail_mask.sum())

for level in ["Novice", "Intermediate", "Expert"]:
    mask = df["Experience_Level"] == level
    if level == "Novice":
        df.loc[mask, "Completion_Time_Sec"] = np.random.normal(200, 100, mask.sum()).astype(int)
    elif level == "Intermediate":
        df.loc[mask, "Completion_Time_Sec"] = np.random.normal(140, 60, mask.sum()).astype(int)
    else:
        df.loc[mask, "Completion_Time_Sec"] = np.random.normal(90, 40, mask.sum()).astype(int)

df["Completion_Time_Sec"] = df["Completion_Time_Sec"].clip(lower=10)

output_path = Path(__file__).resolve().parent / "sample_ux_test_data.xlsx"
df.to_excel(output_path, index=False)

print(f"Sample file created: {output_path}")
print(f"Rows: {len(df)}")
print(df.head(10))
