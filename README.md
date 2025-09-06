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
  A[Data Preparation: Load CSV, parse dates, clean numeric, apply filters] --> B[Baseline Estimation: Use first N points to compute mu0 and sigma0]

  B --> C{Choose Method}

  %% EWMA & CUSUM
  subgraph M1[EWMA & CUSUM Control Charts]
    direction TB
    C --> E1[EWMA: alpha smoothing, L limits, UCL/LCL = mu0 ± L·sigma]
    E1 --> E2[Signal when EWMA outside limits]

    C --> C1[CUSUM: k = shift/2, h = decision interval, track cp and cm]
    C1 --> C2[Signal when cp > h or cm > h]
  end

  %% Rolling SPC
  subgraph M2[Rolling SPC (Z-Score Monitoring)]
    direction TB
    C --> R1[Rolling mean and std over window w]
    R1 --> R2[Z-score = (x - mean)/std]
    R2 --> R3[Outlier when |Z| > threshold, ±3σ band shown]
  end

  %% Rolling Correlation
  subgraph M3[Rolling Correlation (Bivariate SPC)]
    direction TB
    C --> RC1[Inputs: feature_x and feature_y]
    RC1 --> RC2[Compute Pearson r within window w]
    RC2 --> RC3[Calculate p-value via t-test]
    RC3 --> RC4[Significant if p < alpha]
  end

  %% Outputs
  E2 --> O
  C2 --> O
  R3 --> O
  RC4 --> O

  subgraph O[Outputs and Interpretation]
    direction TB
    O1[Charts: EWMA/CUSUM, rolling mean ±3σ, rolling correlation]
    O2[Tables: Alerts and outliers with labels and timestamps]
    O3[Interpretation: EWMA detects subtle shifts, CUSUM persistent drifts, Rolling SPC short anomalies, Rolling Corr stability of relationships]
  end

