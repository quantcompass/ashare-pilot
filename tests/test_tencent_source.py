"""TencentSource 测试：mock akshare，不联网。

腾讯接口 stock_zh_a_hist_tx：symbol 需 sz/sh 前缀；返回列
date/open/close/high/low/amount（无 volume）。
"""

from __future__ import annotations

import pandas as pd
import pytest

from ashare_pilot.datasource.tencent_source import TencentSource, _to_prefixed


def _fake_tx_df():
    return pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "open": [1715.18, 1700.00],
            "close": [1685.01, 1690.00],
            "high": [1718.19, 1710.00],
            "low": [1665.58, 1680.00],
            "amount": [3.43e9, 2.50e9],
        }
    )


@pytest.mark.parametrize(
    "code,expected",
    [
        ("600519", "sh600519"),   # 6 开头 -> 沪
        ("000001", "sz000001"),   # 0 开头 -> 深
        ("301171", "sz301171"),   # 创业板 3 -> 深
        ("688981", "sh688981"),   # 科创 688 -> 沪
    ],
)
def test_symbol_prefix(code, expected):
    assert _to_prefixed(code) == expected


def test_maps_to_contract_volume_absent(monkeypatch):
    captured = {}

    def fake_hist(symbol, start_date, end_date, adjust):
        captured["symbol"] = symbol
        return _fake_tx_df()

    import akshare as ak
    monkeypatch.setattr(ak, "stock_zh_a_hist_tx", fake_hist)

    df = TencentSource().fetch_daily("600519", "20240102", "20240103")
    # 契约核心列齐全
    for c in ("open", "high", "low", "close"):
        assert c in df.columns
    assert df.index.name == "date"
    assert df.index[0] == pd.Timestamp("2024-01-02")
    assert list(df["close"]) == [1685.01, 1690.00]
    assert "amount" in df.columns
    # 腾讯无 volume：列缺失或全空都可接受，但契约必须通过
    assert captured["symbol"] == "sh600519"
    assert df["close"].dtype == "float64"
