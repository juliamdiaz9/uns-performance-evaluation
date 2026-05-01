"""
process_data.py
===============
MQTT Broker Performance Dataset - Preprocessing Pipeline

Description
-----------
This script processes raw CSV files exported from Grafana containing MQTT broker
performance metrics. Each CSV file represents a single metric time series collected
from an EMQX broker monitored over two independent experimental sessions.

The two sessions correspond to different load-balancing/scheduling strategies
evaluated in the thesis:
  - Session 1 (Schultz Method): 2025-11-05, 13:54 – 15:52 UTC-5
  - Session 2 (Parris Method):  2025-11-06, 13:58 – 15:56 UTC-5

For each metric, the script:
  1. Parses and sorts the raw time series by timestamp.
  2. Extracts a fixed-length block of N_POINTS consecutive samples starting at
     the nominal session start time (first sample with Time >= start).
  3. Aligns both blocks by truncating to the shortest available length.
  4. Produces a unified DataFrame with columns:
       Time            – timestamps from Session 1
       Schultz Method  – metric values from Session 1
       Parris Method   – metric values from Session 2
  5. Writes each metric as a separate sheet in the output Excel workbook.

Input
-----
  Raw CSV files located in the same directory as this script.
  Expected CSV columns: Time, Schultz Method, Parris Method
  Expected Time format: YYYY-MM-DD HH:MM:SS

Output
------
  resultado.xlsx – Excel workbook with one sheet per metric,
                   ready for visualization in MATLAB.

Dependencies
------------
  pandas    >= 1.3
  xlsxwriter >= 3.0   (or openpyxl as fallback)

Usage
-----
  python process_data.py

Author
------
  Juliam Diaz – Master's Thesis, 2025
"""

import os
import glob
import pandas as pd

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Root directory: same folder as this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Input folder containing raw CSV files
INPUT_FOLDER = os.path.join(SCRIPT_DIR, "..", "data", "raw")

# Output Excel workbook path
OUTPUT_EXCEL = os.path.join(SCRIPT_DIR, "..", "data", "processed", "mqtt_metrics_processed.xlsx")

# =============================================================================
# EXPERIMENT SESSION TIME BOUNDARIES
# =============================================================================

# Session 1 – Schultz Method
INTERVAL1_START = pd.to_datetime("2025-11-05 13:54:00", format="%Y-%m-%d %H:%M:%S")
INTERVAL1_END   = pd.to_datetime("2025-11-05 15:52:00", format="%Y-%m-%d %H:%M:%S")

# Session 2 – Parris Method
INTERVAL2_START = pd.to_datetime("2025-11-06 13:58:00", format="%Y-%m-%d %H:%M:%S")
INTERVAL2_END   = pd.to_datetime("2025-11-06 15:56:00", format="%Y-%m-%d %H:%M:%S")

# Number of consecutive samples to extract per session
N_POINTS = 60


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def sanitize_sheet_name(name: str) -> str:
    """
    Sanitize a string to be used as a valid Excel sheet name.

    Excel constraints applied:
      - Maximum length: 31 characters
      - Forbidden characters replaced with underscores: : \\ / ? * [ ]

    Parameters
    ----------
    name : str
        Raw candidate sheet name (typically derived from the CSV filename).

    Returns
    -------
    str
        Sanitized sheet name safe for use in an Excel workbook.
    """
    invalid_chars = [":", "\\", "/", "?", "*", "[", "]"]
    for ch in invalid_chars:
        name = name.replace(ch, "_")
    return name[:31]


def extract_session_block(
    df_sorted: pd.DataFrame,
    start_time: pd.Timestamp,
    n_points: int = 60
) -> pd.DataFrame:
    """
    Extract a contiguous block of samples starting at or after a given timestamp.

    The function locates the first row with Time >= start_time and returns the
    next n_points consecutive rows. This approach is robust to irregular sampling
    intervals and guarantees temporal continuity within the extracted block.

    Parameters
    ----------
    df_sorted : pd.DataFrame
        Time-sorted DataFrame with at least a 'Time' column (datetime64).
    start_time : pd.Timestamp
        Nominal session start time. Extraction begins at the first sample
        satisfying Time >= start_time.
    n_points : int, optional
        Desired number of samples to extract (default: 60).

    Returns
    -------
    pd.DataFrame
        Subset of df_sorted with reset integer index. May contain fewer than
        n_points rows if insufficient data is available after start_time.

    Warnings
    --------
    Prints a warning to stdout if no data exists after start_time, or if
    fewer than n_points samples are available.
    """
    # Retain only rows at or after the session start boundary
    df_after = df_sorted.loc[df_sorted["Time"] >= start_time].reset_index(drop=True)

    if df_after.empty:
        print(f"  [WARNING] No samples found with Time >= {start_time}. "
              f"Returning empty DataFrame.")
        return df_after

    if len(df_after) < n_points:
        print(
            f"  [WARNING] Only {len(df_after)} samples available after {start_time} "
            f"(requested {n_points}). Using all available samples."
        )
        return df_after.copy()

    return df_after.iloc[:n_points].copy()


def process_csv_file(csv_path: str) -> pd.DataFrame:
    """
    Load a raw metric CSV and produce an aligned two-session DataFrame.

    Processing steps:
      1. Read CSV and parse the 'Time' column as datetime.
      2. Sort by time to ensure monotonic ordering.
      3. Extract Session 1 block -> provides Time axis and Schultz Method values.
      4. Extract Session 2 block -> provides Parris Method values.
      5. Truncate both blocks to the minimum available length for alignment.
      6. Return a DataFrame with columns: Time, Schultz Method, Parris Method.

    Parameters
    ----------
    csv_path : str
        Absolute or relative path to the input CSV file.

    Returns
    -------
    pd.DataFrame
        Aligned DataFrame with columns [Time, Schultz Method, Parris Method].
        Returns an empty DataFrame with those columns if alignment fails.
    """
    filename = os.path.basename(csv_path)
    print(f"  Processing: {filename}")

    # --- Load and parse ---
    df = pd.read_csv(csv_path)
    df["Time"] = pd.to_datetime(df["Time"], format="%Y-%m-%d %H:%M:%S")
    df_sorted = df.sort_values("Time").reset_index(drop=True)

    # --- Extract session blocks ---
    # Session 1: Time index + Schultz Method values
    block1 = extract_session_block(df_sorted, INTERVAL1_START, n_points=N_POINTS)
    block1 = block1[["Time", "Schultz Method"]].reset_index(drop=True)

    # Session 2: Parris Method values (uses the 'Schultz Method' column from
    # the second session's CSV, which represents the same metric under a
    # different scheduling strategy)
    block2 = extract_session_block(df_sorted, INTERVAL2_START, n_points=N_POINTS)
    block2 = block2[["Schultz Method"]].reset_index(drop=True)

    # --- Align block lengths ---
    min_len = min(len(block1), len(block2))

    if min_len == 0:
        print(f"  [ERROR] One or both session blocks are empty for '{filename}'. "
              f"Skipping.")
        return pd.DataFrame(columns=["Time", "Schultz Method", "Parris Method"])

    if min_len < N_POINTS:
        print(
            f"  [WARNING] Aligned block length is {min_len} samples "
            f"(target was {N_POINTS}) for '{filename}'."
        )

    block1 = block1.iloc[:min_len].copy()
    block2 = block2.iloc[:min_len].copy()

    # Rename Session 2 column to its semantic label
    block1["Parris Method"] = block2["Schultz Method"].values

    print(f"    Schultz Method mean: {block1['Schultz Method'].mean():.4f}")
    print(f"    Parris Method  mean: {block1['Parris Method'].mean():.4f}")

    return block1


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def main():
    """
    Execute the full preprocessing pipeline.

    Discovers all CSV files in INPUT_FOLDER, processes each one, and writes
    the resulting DataFrames as individual sheets in OUTPUT_EXCEL.
    """
    print("=" * 60)
    print("MQTT Broker Metrics – Preprocessing Pipeline")
    print("=" * 60)

    # Discover raw CSV files
    csv_files = sorted(glob.glob(os.path.join(INPUT_FOLDER, "*.csv")))

    if not csv_files:
        print(f"[ERROR] No CSV files found in: {INPUT_FOLDER}")
        return

    print(f"Found {len(csv_files)} CSV file(s) in '{INPUT_FOLDER}'.\n")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_EXCEL), exist_ok=True)

    # Write all processed sheets into a single Excel workbook
    with pd.ExcelWriter(OUTPUT_EXCEL, engine="xlsxwriter") as writer:
        for csv_path in csv_files:
            base_name    = os.path.basename(csv_path)
            sheet_name   = sanitize_sheet_name(os.path.splitext(base_name)[0])

            processed_df = process_csv_file(csv_path)
            processed_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"\n[OK] Output workbook written to:\n     {os.path.abspath(OUTPUT_EXCEL)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
