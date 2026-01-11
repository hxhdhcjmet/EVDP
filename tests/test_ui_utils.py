import io
import pandas as pd
from core.ui_utils import load_file_with_timeout, quality_report, validate_mutual_exclusive, validate_dependencies


class InlineFile(io.BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


def test_load_file_with_timeout_csv():
    data = b"a,b\n1,2\n3,4\n"
    f = InlineFile(data, "test.csv")
    df = load_file_with_timeout(f, timeout=2)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2


def test_quality_report_missing_and_outliers():
    df = pd.DataFrame({
        "x": [1, 2, None, 1000],
        "y": [0.0, 0.1, 0.2, 0.3],
    })
    rep = quality_report(df)
    assert "missing" in rep and "outliers" in rep
    assert rep["missing"].loc["x", "missing_count"] == 1
    assert rep["missing"].loc["x", "missing_ratio"] > 0
    assert "outlier_count" in rep["outliers"].columns


def test_validate_mutual_exclusive():
    errs = validate_mutual_exclusive({"PCA", "插值"})
    assert errs, "PCA与插值应互斥"


def test_validate_dependencies():
    errs = validate_dependencies({"拟合"}, {"dp_ready": False, "interpolated": False})
    assert any("分析器" in e or "插值" in e for e in errs)

