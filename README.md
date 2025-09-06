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
  A[Data Preparation<br/>• Load CSV → pandas<br/>• Parse date/index<br/>• Clean/coerce numeric (handles %)<br/>• Optional filters (date/status)] --> B[Baseline Estimation<br/>• Use first N points<br/>• μ₀ (mean), σ₀ (std)]

  B --> C{Choose Method}

  %% EWMA & CUSUM
  subgraph M1[EWMA & CUSUM Control Charts]
    direction TB
    C --> E1[EWMA<br/>• α (smoothing)<br/>• L (limits)<br/>Compute EWMA_t<br/>UCL/LCL = μ₀ ± L·σ_EWMA]
    E1 --> E2[Signal: EWMA_t outside UCL/LCL]

    C --> C1[CUSUM (two-sided)<br/>• k = shift/2<br/>• h = decision interval<br/>Compute cp_t, cm_t (cumulative deviations)]
    C1 --> C2[Signal: cp_t > h or cm_t > h]
  end

  %% Rolling SPC
  subgraph M2[Rolling SPC (Z-Score Monitoring)]
    direction TB
    C --> R1[Rolling Stats (window = w)<br/>μ_w, σ_w]
    R1 --> R2[Z = (x - μ_w)/σ_w]
    R2 --> R3[Outlier: |Z| > z_thresh<br/>±3σ band for context]
  end

  %% Rolling Correlation
  subgraph M3[Rolling Correlation (Bivariate SPC)]
    direction TB
    C --> RC1[Inputs: feature_x, feature_y]
    RC1 --> RC2[Within window w: Pearson r]
    RC2 --> RC3[p-value via t-test (df = w - 2)]
    RC3 --> RC4[Significant if p < α]
  end

  %% Outputs
  E2 --> O
  C2 --> O
  R3 --> O
  RC4 --> O

  subgraph O[Outputs & Interpretation]
    direction TB
    O1[Charts:<br/>• EWMA/CUSUM with limits<br/>• Rolling mean ±3σ band<br/>• Rolling r colored by significance]
    O2[Tables:<br/>• Alert/Outlier rows with labels & timestamps]
    O3[Interpretation:<br/>• EWMA → subtle mean shifts<br/>• CUSUM → persistent drifts<br/>• Rolling SPC → short-term anomalies<br/>• Rolling Corr → stability of X–Y relation]
  end

  %% Notes
  classDef note fill:#f7f7f7,stroke:#bbb,color:#333;
  N1:::note --- N1[(Tune parameters:<br/>α, L, k, h, w, z_thresh, α (sig))] --- O
