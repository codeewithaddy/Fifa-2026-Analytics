import pandas as pd

# ─────────────────────────────────────────────
#  FIFA 2026 World Cup — Data Exploration Script
#  Run: python explore.py
# ─────────────────────────────────────────────

DATA_PATH = "data/players.csv"

print("=" * 60)
print("  FIFA 2026 — Dataset Exploration")
print("=" * 60)

# 1. Load the dataset
df = pd.read_csv(DATA_PATH)

# 2. Basic shape info
print(f"\n[FILE] Loaded : {DATA_PATH}")
print(f"[SHAPE] Rows  : {df.shape[0]}  |  Columns: {df.shape[1]}")

# 3. Exact column names
print("\n--- COLUMN NAMES (Schema) ---")
print(df.columns.tolist())

# 4. First 5 rows
print("\n--- FIRST 5 ROWS ---")
pd.set_option("display.max_columns", 10)   # keep terminal readable
pd.set_option("display.width", 120)
print(df.head(5))

# 5. Data types & null counts (bonus - useful for Feature Engineering)
print("\n--- COLUMN DATA TYPES & NULL COUNTS ---")
null_info = pd.DataFrame({
    "dtype":      df.dtypes,
    "null_count": df.isnull().sum(),
    "null_%":     (df.isnull().sum() / len(df) * 100).round(1)
})
print(null_info.to_string())

print("\n" + "=" * 60)
print("  Exploration complete.")
print("  Next: Step 2 - Feature Engineering & ML Modeling.")
print("=" * 60)
