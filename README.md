# Control Chart Workflows

This repository contains Python implementations of statistical process control (SPC) and monitoring techniques for time series data. The code blocks are generalized to work with arbitrary CSV datasets, making them adaptable to a wide range of applications.

---

## Workflow Overview
1. **Data Preparation**  
   - Load CSV file(s) into a `pandas` DataFrame.  
   - Parse timestamp or index columns.  
   - Clean and coerce numeric values (handles `%` strings).  
   - Apply optional filters (e.g., by date or status).  

2. **Baseline Estimation**  
   - Use the first *N* observations (configurable) to compute the mean (`μ₀`) and standard deviation (`σ₀`).  
   - Provides reference values for control limits.

3. **Control Chart Methods**  
   - **EWMA & CUSUM Control Charts** (`control_charts_generic.py`)  
   - **Rolling Statistical Process Control** (`spc_rolling_generic.py`)  
   - **Rolling Correlation Analysis** (`rolling_correlation_spc_generic.py`)  

4. **Visualization**  
   - Generate control charts with annotated signals.  
   - Provide outlier/signal summary tables for interpretation.

---

## Methods Embedded

### 1. EWMA (Exponentially Weighted Moving Average)
- **Purpose**: Detect small, sustained shifts in the process mean.  
- **Method**: Weighted moving average of the selected metric with smoothing factor `α`.  
- **Control Limits**: Upper and lower limits at `μ₀ ± Lσ`.  
- **Signals**: Points outside the control limits indicate potential process drift.

### 2. CUSUM (Cumulative Sum)
- **Purpose**: Detect persistent deviations from the mean, even when individual points remain within limits.  
- **Method**: Tracks cumulative positive and negative deviations, with allowance `k` and decision interval `h`.  
- **Signals**: Triggered when cumulative deviations exceed `h`, suggesting systematic process change.

### 3. Rolling SPC (Z-Score Monitoring)
- **Purpose**: Identify short-term outliers against recent process behavior.  
- **Method**: Compute rolling mean and standard deviation over a fixed window.  
- **Control Limits**: ±3σ band around the rolling mean.  
- **Signals**: Observations with |Z| > threshold (default 1.645 for ~90% CI) flagged as outliers.

### 4. Rolling Correlation (Bivariate SPC)
- **Purpose**: Track stability of the linear relationship between two features over time.  
- **Method**: Compute rolling Pearson correlation coefficient `r` within a window, test significance using Student’s t-distribution.  
- **Signals**: Highlights when the correlation between features is statistically significant (p < α).

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
- Adjust column names (`date_col`, `value_col`, `x_col`, `y_col`, etc.) in the scripts.  
- Point `file_path` to your dataset.  
- Tune parameters (`α`, `L`, `k`, `h`, `window`, `z_thresh`, `alpha`) based on process sensitivity.  

```mermaid
flowchart TD
  A[Data preparation: load CSV, parse dates, clean numeric, optional filters] --> B[Baseline estimation: first N points to compute mu0 and sigma0]
  B --> C{Method}

  C --> E[EWMA: alpha and L define limits from mu0 and sigma]
  E --> E_sig[Signal when EWMA is outside limits]

  C --> S[CUSUM: parameters k and h]
  S --> S_sig[Signal when cp exceeds h or cm exceeds h]

  C --> R[Rolling SPC: rolling mean and std over window w]
  R --> R_sig[Signal when abs Z is greater than threshold; show plus or minus 3 std band]

  C --> RC[Rolling correlation: Pearson r over window w]
  RC --> RC_sig[Signal when p value is less than alpha]

  E_sig --> O[Outputs: charts and alert table]
  S_sig --> O
  R_sig --> O
  RC_sig --> O
