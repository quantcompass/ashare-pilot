"""数据源层测试：放宽后的数据契约、腾讯源、fallback、缓存。"""

from __future__ import annotations

import pandas as pd
import pytest

from ashare_pilot.datasource.base import CORE_COLUMNS, validate


def _df(index, **cols):
    """构造一个 date 索引的行情 DataFrame。"""
    idx = pd.DatetimeIndex(pd.to_datetime(index), name="date")
    return pd.DataFrame(cols, index=idx)


# ---------- 数据契约（放宽后）----------

def test_validate_passes_with_only_core_columns():
    """只有 OHLC（无 volume）也应通过——腾讯源就是这种。"""
    df = _df(
        ["2024-01-01", "2024-01-02"],
        open=[1.0, 2.0], high=[1.0, 2.0], low=[1.0, 2.0], close=[1.0, 2.0],
    )
    assert validate(df) is df  # 原样返回


def test_validate_fails_when_core_column_missing():
    """缺核心列（如 close）必须报错。"""
    df = _df(
        ["2024-01-01"],
        open=[1.0], high=[1.0], low=[1.0],  # 缺 close
    )
    with pytest.raises(ValueError, match="close"):
        validate(df)


def test_validate_fails_on_wrong_index_name():
    df = pd.DataFrame(
        {c: [1.0] for c in CORE_COLUMNS},
        index=pd.DatetimeIndex(["2024-01-01"], name="dt"),  # 错误索引名
    )
    with pytest.raises(ValueError, match="date"):
        validate(df)


def test_validate_allows_optional_volume_and_amount():
    """volume / amount 作为可选列存在时也通过。"""
    df = _df(
        ["2024-01-01"],
        open=[1.0], high=[1.0], low=[1.0], close=[1.0],
        volume=[100.0], amount=[1000.0],
    )
    assert validate(df) is df
