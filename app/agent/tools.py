import pandas as pd
from fastapi import UploadFile


def _read_csv(upload: UploadFile) -> pd.DataFrame:
    """
    Read uploaded CSV safely.
    Rewinds the underlying file pointer so multiple tools can read the same file.
    """
    try:
        upload.file.seek(0)
    except Exception:
        pass
    return pd.read_csv(upload.file)


def generate_summary_statistics(file: UploadFile) -> str:
    df = _read_csv(file)

    if df.empty:
        return "⚠️ CSV has 0 rows (nothing to summarize)."

    # include="all" gives more helpful output when there are non-numeric columns too
    summary = df.describe(include="all")
    return summary.to_string()


def detect_missing_values(file: UploadFile) -> str:
    df = _read_csv(file)

    total_rows = len(df)
    total_cols = len(df.columns)

    if total_rows == 0:
        return "⚠️ CSV has 0 rows (nothing to analyze)."
    if total_cols == 0:
        return "⚠️ CSV has 0 columns (nothing to analyze)."

    missing_counts = df.isnull().sum()
    missing_counts = missing_counts[missing_counts > 0]

    if missing_counts.empty:
        return f"✅ No missing values found. (rows={total_rows}, cols={total_cols})"

    summary_df = (
        pd.DataFrame({
            "column": missing_counts.index.astype(str),
            "missing": missing_counts.values.astype(int),
        })
        .assign(percent=lambda d: (d["missing"] / total_rows * 100))
        .sort_values(["missing", "column"], ascending=[False, True])
        .reset_index(drop=True)
    )

    total_missing_cells = int(summary_df["missing"].sum())
    summary_df["percent"] = summary_df["percent"].map(lambda x: f"{x:.2f}%")

    table = summary_df.to_string(index=False)

    return (
        f"Missing Values Summary\n"
        f"- rows: {total_rows}\n"
        f"- cols: {total_cols}\n"
        f"- total missing cells: {total_missing_cells}\n\n"
        f"{table}"
    )


TOOL_REGISTRY = {
    "Generate summary statistics": generate_summary_statistics,
    "Detect missing values": detect_missing_values,
}

# Simple alias keywords to improve intent matching.
# Keep these lowercase and short for robust substring checks.
TOOL_ALIASES = {
    "Generate summary statistics": [
        "summary",
        "summarize",
        "stats",
        "statistics",
        "describe",
        "data stats",
        "profiling",
        "overview",
        "basic stats",
    ],
    "Detect missing values": [
        "missing",
        "missing values",
        "null",
        "nan",
        "empty",
        "blank",
    ],
}
