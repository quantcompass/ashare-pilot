"""成本估算测试：VWAP、筹码分布、现价上下方占比。纯函数，不联网。

对应方法论 §6：用 VWAP + 成交密集区做"市场平均成本"的粗略代理
(非真实主力成本)。
"""

from __future__ import annotations

import pandas as pd
import pytest

from ashare_pilot.analysis import cost


def _df(rows):
    """rows: (high, low, close, volume)。"""
    idx = pd.DatetimeIndex(
        pd.to_datetime([f"2026-01-{i+1:02d}" for i in range(len(rows))]), name="date"
    )
    return pd.DataFrame(
        {
            "open": [r[2] for r in rows],
            "high": [r[0] for r in rows],
            "low": [r[1] for r in rows],
            "close": [r[2] for r in rows],
            "volume": [r[3] for r in rows],
        },
        index=idx, dtype="float64",
    )


def test_typical_price():
    df = _df([(11, 9, 10, 100)])
    # (11+9+10)/3 = 10
    assert cost.typical_price(df).iloc[0] == pytest.approx(10.0)


def test_vwap_weighted_by_volume():
    # 第1天 tp=10 量100；第2天 tp=11 量300 -> (10*100+11*300)/400 = 10.75
    df = _df([(11, 9, 10, 100), (12, 10, 11, 300)])
    assert cost.vwap(df) == pytest.approx(10.75)


def test_vwap_single_row():
    df = _df([(11, 9, 10, 100)])
    assert cost.vwap(df) == pytest.approx(10.0)


def test_chip_distribution_finds_dense_zone():
    # 大量成交集中在 ~20 元，少量在 ~50 元
    rows = [(21, 19, 20, 1000), (21, 19, 20, 1000), (51, 49, 50, 100)]
    dist = cost.chip_distribution(df=_df(rows), bin_width=2.0)
    # 占比之和为 1，且最密集档应在 20 附近、占比最高
    assert dist.sum() == pytest.approx(1.0)
    top = dist.index[0]
    assert top.left <= 20 <= top.right
    assert dist.iloc[0] > 0.8  # 20元附近占绝大多数


def test_position_ratio_below_above():
    # 价格分布：两天在20(量100+100=200)，一天在50(量100) -> 现价30
    rows = [(21, 19, 20, 100), (21, 19, 20, 100), (51, 49, 50, 100)]
    below, above = cost.position_ratio(_df(rows), price=30.0)
    assert below == pytest.approx(200 / 300)   # 20元的在下方
    assert above == pytest.approx(100 / 300)   # 50元的在上方


def test_position_ratio_sums_to_one_when_no_tie():
    rows = [(21, 19, 20, 100), (51, 49, 50, 100)]
    below, above = cost.position_ratio(_df(rows), price=35.0)
    assert below + above == pytest.approx(1.0)
