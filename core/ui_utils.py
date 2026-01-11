import pandas as pd
import numpy as np
from typing import Dict, Set, List
from concurrent.futures import ThreadPoolExecutor

def load_file_with_timeout(file, timeout: int = 10) -> pd.DataFrame:
    """CHANGED v2.1
    Load CSV/Excel file with a timeout.

    Args:
        file: Streamlit UploadedFile-like object
        timeout: Maximum seconds to wait

    Returns:
        Loaded DataFrame

    Raises:
        TimeoutError: When reading exceeds timeout
        ValueError: When unsupported extension
    """
    def _read():
        name = getattr(file, "name", "")
        if name.endswith(".csv"):
            return pd.read_csv(file)
        elif name.endswith(".xlsx"):
            return pd.read_excel(file)
        raise ValueError("仅支持CSV或Excel文件")

    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_read)
        return fut.result(timeout=timeout)


def quality_report(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """CHANGED v2.1
    Build a data quality report including missing stats and outlier detection.

    Args:
        df: Input DataFrame

    Returns:
        Dict with keys:
            - missing: DataFrame with columns [missing_count, missing_ratio]
            - outliers: DataFrame with columns [outlier_count, outlier_ratio]
    """
    if df is None or df.empty:
        return {
            "missing": pd.DataFrame(columns=["missing_count", "missing_ratio"]),
            "outliers": pd.DataFrame(columns=["outlier_count", "outlier_ratio"]),
        }

    miss_count = df.isna().sum()
    miss_ratio = miss_count / len(df)
    missing = pd.DataFrame({
        "missing_count": miss_count,
        "missing_ratio": miss_ratio.round(4),
    })

    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not num_cols:
        outliers = pd.DataFrame(columns=["outlier_count", "outlier_ratio"])
    else:
        z = (df[num_cols] - df[num_cols].mean()) / df[num_cols].std(ddof=0)
        mask = (np.abs(z) > 3)
        out_count = mask.sum()
        out_ratio = out_count / len(df)
        outliers = pd.DataFrame({
            "outlier_count": out_count,
            "outlier_ratio": out_ratio.round(4),
        })

    return {"missing": missing, "outliers": outliers}


def validate_mutual_exclusive(selected_opts: Set[str]) -> List[str]:
    """CHANGED v2.1
    Validate mutual exclusivity among option panel selections.

    Args:
        selected_opts: Selected option names

    Returns:
        List of error messages if conflict exists
    """
    errors: List[str] = []
    if "PCA" in selected_opts and ("插值" in selected_opts or "拟合" in selected_opts):
        errors.append("PCA与插值/拟合互斥，请分步执行")
    return errors


def validate_dependencies(selected_opts: Set[str], state: Dict[str, bool]) -> List[str]:
    """CHANGED v2.1
    Validate dependencies for chosen options.

    Args:
        selected_opts: Selected option names
        state: Dict of runtime flags, keys: dp_ready, interpolated

    Returns:
        List of error messages
    """
    errors: List[str] = []
    dp_ready = state.get("dp_ready", False)
    interpolated = state.get("interpolated", False)
    if "插值" in selected_opts and not dp_ready:
        errors.append("请先初始化插值拟合分析器")
    if "拟合" in selected_opts and not dp_ready:
        errors.append("请先初始化插值拟合分析器")
    if "拟合" in selected_opts and not interpolated:
        errors.append("拟合依赖插值结果，请先完成插值")
    return errors

