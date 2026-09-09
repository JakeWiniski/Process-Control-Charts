# Control Chart Workflows

This repository contains Python implementations of statistical process control (SPC) and monitoring techniques for time series data. The code blocks are generalized to work with arbitrary CSV datasets, making them adaptable to a wide range of applications.

---

## Workflow Overview
1. **Data Preparation**  
   - Load CSV file(s) into a `pandas` DataFrame.  
   - Parse timestamp or index columns.  
   - Clean and coerce numeric values (handles `%` strings).  
   - Apply optional filters (a minimum date in every script; the EWMA/CUSUM script also supports arbitrary column-value filters via `FILTERS`).  

2. **Baseline Estimation** *(EWMA & CUSUM only)*  
   - Use the first *N* observations (`baseline_window`, configurable) to compute the mean (`μ₀`) and standard deviation (`σ₀`).  
   - Provides the fixed reference values for the EWMA/CUSUM control limits. (The rolling SPC and rolling correlation charts instead recompute statistics over a moving window.)

3. **Control Chart Methods**  
   - **EWMA & CUSUM Control Charts** (`EWMA_CUSUM_control_chart.py`)  
   - **Rolling Statistical Process Control** (`spc_rolling_control_chart.py`)  
   - **Rolling Correlation Analysis** (`rolling_correlation_control_chart.py`)  

4. **Visualization**  
   - Generate control charts with annotated signals.  
   - The EWMA & CUSUM script also prints a combined alert table of flagged points; the rolling SPC and rolling correlation scripts communicate signals through the plot (colored/marked points).

---

## Methods Embedded

### 1. EWMA (Exponentially Weighted Moving Average)
- **Purpose**: Detect small, sustained shifts in the process mean.  
- **Method**: Weighted moving average of the selected metric with smoothing factor `α`, seeded at the baseline mean (`z₀ = μ₀`).  
- **Control Limits**: Time-varying limits at `μ₀ ± L·σ_EWMA(t)`, where `σ_EWMA(t) = σ₀·√((α/(2−α))·(1−(1−α)^{2t}))`. Limits are tighter for the earliest points and widen to the steady-state value `σ₀·√(α/(2−α))`.  
- **Signals**: Points outside the control limits indicate potential process drift.

### 2. CUSUM (Cumulative Sum)
- **Purpose**: Detect persistent deviations from the mean, even when individual points remain within limits.  
- **Method**: Tracks cumulative positive and negative deviations, with allowance `k` and decision interval `h`.  
- **Signals**: Triggered when cumulative deviations exceed `h`, suggesting systematic process change.

### 3. Rolling SPC (Z-Score Monitoring)
- **Purpose**: Identify short-term outliers against recent process behavior.  
- **Method**: For each point, compute the mean and standard deviation of the `window` points that *precede* it, then z-score the point against that history (the point is excluded from its own window so it can't mask its own anomaly).  
- **Control Limits**: ±`z_thresh`σ band around the rolling mean (default 3.0 = conventional ±3σ, ~99.7%), matching the outlier test so flagged points fall outside the band.  
- **Signals**: Observations with |Z| > `z_thresh` flagged as outliers.

### 4. Rolling Correlation (Bivariate SPC)
- **Purpose**: Track stability of the linear relationship between two features over time.  
- **Method**: Compute rolling Pearson correlation coefficient `r` within a window, test significance using Student’s t-distribution.  
- **Signals**: Highlights windows where the correlation is nominally significant (p < α). Treat these flags as **descriptive**, not a controlled test: the windows overlap (so adjacent p-values are correlated) and running one test per window inflates false positives (~`α·N` chance flags). Read stretches of flagged windows rather than isolated ones; tighten `α` (e.g. Bonferroni `α/N`) for a stricter view.

---

## Practical Interpretation

- **EWMA**  
  Use when interested in subtle process shifts.  
  *Example*: A gradual drift in product quality, temperature stability, or sensor bias.

- **CUSUM**  
  Use when monitoring for persistent deviations.  
  *Example*: A machine that gradually produces parts outside tolerance.

- **Rolling SPC**  
  Use when focusing on short-term outliers relative to recent performance.  
  *Example*: Identifying single bad batches or short-lived anomalies.

- **Rolling Correlation**  
  Use when the relationship between two variables matters as much as their values.  
  *Example*: Monitoring whether higher input moisture consistently predicts higher conversion rate.

---

## Usage
- Adjust column names (`time_col`/`date_col`, `value_col`, `x_col`, `y_col`, etc.) in the scripts.  
- Point `file_path` to your dataset.  
- Tune parameters (`α`, `L`, `k`, `h`, `window`, `z_thresh`, `alpha`) based on process sensitivity.  

```mermaid
flowchart TD
  A[Data preparation: load CSV, parse dates, clean numeric, optional filters] --> C{Method}

  C --> B[Baseline estimation EWMA/CUSUM only: first N points to compute mu0 and sigma0]
  B --> E[EWMA: alpha and L define time-varying limits from mu0 and sigma, seeded at mu0]
  E --> E_sig[Signal when EWMA is outside limits]

  B --> S[CUSUM: parameters k and h]
  S --> S_sig[Signal when cp exceeds h or cm exceeds h]

  C --> R[Rolling SPC: mean and std over the w points preceding each point]
  R --> R_sig[Signal when abs Z exceeds z_thresh; band is plus or minus z_thresh std, default 3]

  C --> RC[Rolling correlation: Pearson r over window w]
  RC --> RC_sig[Signal when p value is less than alpha]

  E_sig --> O[Outputs: charts; alert table for EWMA/CUSUM]
  S_sig --> O
  R_sig --> O
  RC_sig --> O
