import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# =========================
# Settings (edit as needed)
# =========================
file_path = Path("timeseries.csv")   # CSV path

# Column names in your CSV
date_col   = "date"                  # timestamp column (parseable by pandas.to_datetime)
value_col  = "value"                 # numeric metric to chart (float or % string like "85%")
label_col  = None                    # optional x-axis label column (e.g., "run_id"); if None, auto 1..N

# Optional earliest date (inclusive). Use None to include all.
min_date = None                      # e.g., "2025-01-01" or None

# Rolling SPC params
window  = 7                          # rolling window size (in rows)
z_thresh = 1.645                     # |z| > z_thresh -> outlier (≈90% two-sided); adjust as needed

# Plot options
title_text = f"SPC Chart – {value_col}"
y_min_zero = False                   # set True if your metric is a percentage that should not go below 0

# =========================
# Load and clean
# =========================
df = pd.read_csv(file_path)

# Basic checks
if date_col not in df.columns:
    raise ValueError(f"Expected date column '{date_col}' not found in CSV.")
if value_col not in df.columns:
    raise ValueError(f"Expected value column '{value_col}' not found in CSV.")

# Parse date
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

# Coerce value column:
# - If it's a string with '%', strip and convert to float
# - Else, try to convert directly to numeric
if df[value_col].dtype == object:
    # strip whitespace
    s = df[value_col].astype(str).str.strip()
    # if it contains percent signs, remove and convert
    if s.str.contains("%").any():
        df[value_col] = pd.to_numeric(s.str.replace("%", "", regex=False), errors="coerce")
    else:
        df[value_col] = pd.to_numeric(s, errors="coerce")
else:
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

# Drop missing essentials
df = df.dropna(subset=[date_col, value_col]).copy()

# Optional date filter
if min_date is not None:
    df = df[df[date_col] >= pd.to_datetime(min_date)]

# Sort by date and create label
df = df.sort_values(date_col).reset_index(drop=True)
if label_col and (label_col in df.columns):
    df["__label__"] = df[label_col].astype(str)
else:
    df["__label__"] = (df.index + 1).astype(str)

# =========================
# Rolling SPC calculation
# =========================
df["rolling_mean"] = df[value_col].rolling(window=window, min_periods=window).mean()
df["rolling_std"]  = df[value_col].rolling(window=window, min_periods=window).std(ddof=1)

# Avoid divide-by-zero; mark z only where std > 0
valid = df["rolling_std"] > 0
df["z_score"] = np.nan
df.loc[valid, "z_score"] = (df.loc[valid, value_col] - df.loc[valid, "rolling_mean"]) / df.loc[valid, "rolling_std"]
df["outlier"] = df["z_score"].abs() > z_thresh

# =========================
# Visualization
# =========================
x = np.arange(len(df))

plt.figure(figsize=(14, 6))
plt.plot(x, df[value_col], label=value_col, marker='o')
plt.plot(x, df["rolling_mean"], label=f"{window}-point Rolling Mean", color="orange")

# Control band: ±3σ around rolling mean (only where available)
upper = df["rolling_mean"] + 3 * df["rolling_std"]
lower = df["rolling_mean"] - 3 * df["rolling_std"]
plt.fill_between(x, lower, upper, where=~(upper.isna() | lower.isna()), color="orange", alpha=0.2, label="±3σ Control Limits")

# Outliers
plt.scatter(x[df["outlier"]], df.loc[df["outlier"], value_col], color="red", s=80, label="Outliers")

plt.title(title_text)
plt.xlabel("Index/Label")
plt.ylabel(value_col)
plt.xticks(ticks=x, labels=df["__label__"], rotation=90)
plt.legend()
plt.tight_layout()
if y_min_zero:
    plt.ylim(bottom=0)
plt.show()
