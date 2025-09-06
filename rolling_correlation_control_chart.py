import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import t as student_t

# =========================
# Settings (edit as needed)
# =========================
file_path = Path("timeseries.csv")   # CSV path

# Column names in your CSV
date_col  = "date"                   # time column (parseable by pandas.to_datetime)
x_col     = "feature_x"              # first feature (e.g., moisture)
y_col     = "feature_y"              # second feature (e.g., conversion)
label_col = None                     # optional x-axis labels (e.g., "run_id"); None -> 1..N

# Optional earliest date (inclusive). Use None to include all.
min_date = None                      # e.g., "2025-01-01" or None

# Rolling correlation params
window = 15                          # number of rows per rolling window
alpha  = 0.05                        # significance level for correlation

# =========================
# Load dataset
# =========================
df = pd.read_csv(file_path)

# Basic checks
for c in [date_col, x_col, y_col]:
    if c not in df.columns:
        raise KeyError(f"Expected column '{c}' not found. Available: {list(df.columns)}")

# Parse date
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

# Coerce X/Y to numeric:
# - If strings with '%', strip and convert; else to_numeric directly
def _to_numeric_series(s):
    if s.dtype == object:
        ss = s.astype(str).str.strip()
        if ss.str.contains("%").any():
            return pd.to_numeric(ss.str.replace("%", "", regex=False), errors="coerce")
        return pd.to_numeric(ss, errors="coerce")
    return pd.to_numeric(s, errors="coerce")

df[x_col] = _to_numeric_series(df[x_col])
df[y_col] = _to_numeric_series(df[y_col])

# Drop invalid rows and optional date filter
df = df.dropna(subset=[date_col, x_col, y_col]).copy()
if min_date is not None:
    df = df[df[date_col] >= pd.to_datetime(min_date)]

# Sort chronologically and build labels
df = df.sort_values(date_col).reset_index(drop=True)
if label_col and (label_col in df.columns):
    labels = df[label_col].astype(str).tolist()
else:
    labels = (df.index + 1).astype(str).tolist()

x_idx = np.arange(len(df))
N = len(df)
if N < 2:
    raise ValueError("Not enough rows after filtering to compute rolling correlation.")

# =========================
# Rolling correlation with significance
# =========================
vals_x = df[x_col].to_numpy()
vals_y = df[y_col].to_numpy()

rolling_r = np.full(N, np.nan)
rolling_p = np.full(N, np.nan)

for i in range(window - 1, N):
    a = vals_x[i - window + 1 : i + 1]
    b = vals_y[i - window + 1 : i + 1]
    # Guard against zero-variance windows
    if np.std(a, ddof=1) == 0 or np.std(b, ddof=1) == 0:
        r = np.nan
        p = np.nan
    else:
        r = np.corrcoef(a, b)[0, 1]
        if np.isfinite(r):
            if abs(r) < 1.0:
                t_stat = r * np.sqrt((window - 2) / max(1e-12, (1.0 - r**2)))
                p = 2.0 * student_t.sf(abs(t_stat), df=window - 2)
            else:
                p = 0.0
        else:
            p = np.nan
    rolling_r[i] = r
    rolling_p[i] = p

df["rolling_corr"] = rolling_r
df["rolling_p"]    = rolling_p
df["sig"]          = df["rolling_p"] < alpha

# =========================
# Plot (color-coded by significance)
# =========================
plt.figure(figsize=(14, 6))
plt.plot(x_idx, df["rolling_corr"], linewidth=1, alpha=0.3)

# Non-significant
ns_mask = (~df["sig"]) & df["rolling_corr"].notna()
plt.scatter(x_idx[ns_mask], df.loc[ns_mask, "rolling_corr"],
            label=f"Not significant (p ≥ {alpha})", alpha=0.9)

# Significant
sig_mask = df["sig"] & df["rolling_corr"].notna()
plt.scatter(x_idx[sig_mask], df.loc[sig_mask, "rolling_corr"],
            label=f"Significant (p < {alpha})", alpha=0.9)

plt.axhline(0, linestyle="--", color="gray")
plt.title(f"Rolling Correlation ({window}-point window)\n{x_col} vs {y_col}")
plt.xlabel("Index/Label")
plt.ylabel("Correlation (Pearson r)")
plt.xticks(ticks=x_idx, labels=labels, rotation=90)
plt.axvspan(0, max(0, window - 1), color='gray', alpha=0.1, label=f'Insufficient data (<{window})')
plt.legend()
plt.tight_layout()
plt.show()
