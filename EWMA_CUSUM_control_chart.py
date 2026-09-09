import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# =========================
# Settings (edit as needed)
# =========================
# Where to look for your CSV by default (falls back to /mnt/data if not found)
DATA_DIR = Path.cwd()
if not DATA_DIR.exists():
    DATA_DIR = Path("/mnt/data")

# ---- Input file ----
file_path = DATA_DIR / "timeseries.csv"   # put your CSV name here

# ---- Column names in your CSV ----
time_col  = "time"        # timestamp column (parseable by pandas.to_datetime)
value_col = "value"       # numeric metric to chart (float)
label_col = None          # optional label for x-axis (e.g., "run_id"); if None, will auto-generate

# ---- Optional simple filters (applied before anything else) ----
# Provide as a dict of {column_name: allowed_value or list_of_allowed_values}
# Example: {"status": "ok"} or {"segment": ["A", "B"], "status": "ok"}
FILTERS = {}

# ---- Optional minimum timestamp to include (compared against time_col). Use None to include all. ----
min_date = None   # e.g., "2025-01-01" or None

# ---- Baseline (first N points) for mu0, sigma0 ----
baseline_window = 13

# ---- EWMA params ----
alpha = 0.3
L = 2.5

# ---- CUSUM (two-sided) params ----
# target_shift_sigma is the detectable shift (in sigma units)
target_shift_sigma = 0.5
k = target_shift_sigma / 2.0
h = 4.0

# ---- Plot appearance ----
title_suffix = ""   # e.g., "(segment = X)" if you want a suffix; otherwise ""


# =========================
# Load & prep
# =========================
df = pd.read_csv(file_path)

# Basic sanity checks
if time_col not in df.columns:
    raise ValueError(f"Expected time column '{time_col}' not found in CSV.")
if value_col not in df.columns:
    raise ValueError(f"Expected value column '{value_col}' not found in CSV.")

# Apply simple filters
if FILTERS:
    mask = pd.Series(True, index=df.index)
    for c, allowed in FILTERS.items():
        if c not in df.columns:
            raise ValueError(f"Filter column '{c}' not found in CSV.")
        if isinstance(allowed, (list, tuple, set)):
            mask &= df[c].isin(allowed)
        else:
            mask &= (df[c] == allowed)
    df = df[mask].copy()

# Parse time column
df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

# Coerce the value column to numeric:
# - If it's a string with '%' (e.g., "85%"), strip the sign and convert
# - Otherwise convert directly; non-numeric entries become NaN and are dropped below
if df[value_col].dtype == object:
    s = df[value_col].astype(str).str.strip()
    if s.str.contains("%").any():
        df[value_col] = pd.to_numeric(s.str.replace("%", "", regex=False), errors="coerce")
    else:
        df[value_col] = pd.to_numeric(s, errors="coerce")
else:
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

# Drop rows with bad/missing values
df = df.dropna(subset=[time_col, value_col]).copy()

# Optional time filter
if min_date is not None:
    df = df[df[time_col] >= pd.to_datetime(min_date)]

# Sort by time
df = df.sort_values(time_col).reset_index(drop=True)

# X-axis label column
if label_col and (label_col in df.columns):
    xlabels = df[label_col].astype(str).tolist()
elif "file" in df.columns:
    # if a file column exists, strip extension for a neat label
    xlabels = df["file"].astype(str).str.replace(".csv", "", regex=False).tolist()
else:
    # fallback: use 1..N indexing
    xlabels = (df.index + 1).astype(str).tolist()

x = np.arange(len(df))
if len(df) < 2:
    raise ValueError("Not enough points to chart after filtering. Check your filters or min_date.")

# =========================
# Baseline estimates
# =========================
def _safe_std(series):
    s = series.std(ddof=1)
    if pd.isna(s) or s == 0:
        s = 1e-6
    return float(s)

if len(df) < baseline_window + 5:
    mu0 = float(df[value_col].mean())
    sigma0 = _safe_std(df[value_col])
else:
    baseline = df.loc[:baseline_window-1, value_col]
    mu0 = float(baseline.mean())
    sigma0 = _safe_std(baseline)

# =========================
# --- EWMA ---
# =========================
# Seed the EWMA at the baseline mean (z_0 = mu0), the textbook initialization,
# then apply the recursion z_t = alpha*x_t + (1 - alpha)*z_{t-1}. This anchors
# the statistic to the baseline center rather than to the first observation.
vals = df[value_col].to_numpy()
ewma = np.empty(len(vals))
prev = mu0
for i, xv in enumerate(vals):
    prev = alpha * xv + (1.0 - alpha) * prev
    ewma[i] = prev

# Time-varying control limits. The EWMA variance grows from 0 toward its
# steady-state value, so the exact limits are narrower for early points and
# widen to the asymptotic sigma0*sqrt(alpha/(2-alpha)) as t increases.
t_idx = np.arange(1, len(vals) + 1)
var_factor = (alpha / (2.0 - alpha)) * (1.0 - (1.0 - alpha) ** (2 * t_idx))
sigma_ewma = sigma0 * np.sqrt(var_factor)
ucl_ewma = mu0 + L * sigma_ewma
lcl_ewma = mu0 - L * sigma_ewma
ewma_signal = (ewma > ucl_ewma) | (ewma < lcl_ewma)

# =========================
# --- CUSUM (two-sided) ---
# =========================
z = (df[value_col] - mu0) / sigma0
cp = np.zeros(len(z))
cm = np.zeros(len(z))
cusum_signal = np.zeros(len(z), dtype=bool)

for t in range(len(z)):
    cp[t] = max(0.0, (cp[t-1] if t > 0 else 0.0) + (z.iloc[t] - k))
    cm[t] = max(0.0, (cm[t-1] if t > 0 else 0.0) + (-z.iloc[t] - k))
    if cp[t] > h or cm[t] > h:
        cusum_signal[t] = True

# =========================
# --- Alerts Summary ---
# =========================
ewma_alerts = df.loc[ewma_signal, [time_col, value_col]].copy()
ewma_alerts["chart"] = "EWMA"
ewma_alerts["label"] = np.array(xlabels)[ewma_signal]

cusum_alerts = df.loc[cusum_signal, [time_col, value_col]].copy()
cusum_alerts["chart"] = "CUSUM"
cusum_alerts["label"] = np.array(xlabels)[cusum_signal]

alerts = pd.concat([ewma_alerts, cusum_alerts], ignore_index=True)
alerts = alerts.rename(columns={value_col: "value"})

print("Alerts (if any):")
print(alerts if not alerts.empty else "None")

# =========================
# --- Plots ---
# =========================

# 1) EWMA chart
plt.figure(figsize=(14, 6))
plt.plot(x, df[value_col], marker='o', label=value_col)
plt.plot(x, ewma, label=f"EWMA (alpha={alpha})")
plt.axhline(mu0, linestyle="--", label="Center (mu0)")
plt.plot(x, ucl_ewma, linestyle="--", color="tab:red", label=f"UCL (L={L})")
plt.plot(x, lcl_ewma, linestyle="--", color="tab:red", label=f"LCL (L={L})")
plt.scatter(x[ewma_signal], ewma[ewma_signal], s=80, label="EWMA Signal")
plt.title(f"EWMA Control Chart – {value_col} {title_suffix}".strip())
plt.xlabel("Index/Label")
plt.ylabel(value_col)
plt.xticks(ticks=x, labels=xlabels, rotation=90)
plt.legend()
plt.tight_layout()
plt.show()

# 2) CUSUM chart
plt.figure(figsize=(14, 6))
plt.plot(x, cp, label="CUSUM + (cp)")
plt.plot(x, cm, label="CUSUM − (cm)")
plt.axhline(h, linestyle="--", label=f"Decision interval h={h}")
plt.title(f"CUSUM Control Chart – {value_col}  (k={k:.2f}σ, h={h:.2f}σ) {title_suffix}".strip())
plt.xlabel("Index/Label")
plt.ylabel("CUSUM (σ units)")
plt.xticks(ticks=x, labels=xlabels, rotation=90)
plt.legend()
plt.tight_layout()
plt.show()
