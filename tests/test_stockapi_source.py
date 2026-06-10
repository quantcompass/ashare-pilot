"""StockApiSource 测试：mock HTTP，不联网、不消耗额度。

真实返回（实测）：data 为「行列表」，每行 dict、英文 key、字符串值，
time 为日期字符串(YYYY-MM-DD)，顶层 code==20000 表示成功。
"""

from __future__ import annotations

import pandas as pd
import pytest

from ashare_pilot.datasource.stockapi_source import StockApiSource


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _ok_payload():
    """模拟 stockapi day 接口真实成功返回（两天，行列表、字符串值）。"""
    return {
        "msg": "success",
        "code": 20000,
        "data": [
            {
                "code": "600519.SH", "time": "2024-01-02",
                "open": "1715.18", "high": "1718.19",
                "low": "1665.58", "close": "1685.01",
                "volume": "2031608", "amount": "3430000000",
            },
            {
                "code": "600519.SH", "time": "2024-01-03",
                "open": "1700.00", "high": "1710.00",
                "low": "1680.00", "close": "1690.00",
                "volume": "1500000", "amount": "2500000000",
            },
        ],
    }


def _patch_get(monkeypatch, payload, captured=None):
    def fake_get(url, params=None, timeout=None):
        if captured is not None:
            captured["url"] = url
            captured["params"] = params
        return _FakeResp(payload)
    monkeypatch.setattr(
        "ashare_pilot.datasource.stockapi_source.requests.get", fake_get
    )


def test_maps_row_list_to_contract(monkeypatch):
    _patch_get(monkeypatch, _ok_payload())
    df = StockApiSource(token="TK").fetch_daily("600519", "20240102", "20240103")
    for c in ("open", "high", "low", "close"):
        assert c in df.columns
    assert df.index.name == "date"
    # 字符串值已转 float
    assert list(df["close"]) == [1685.01, 1690.00]
    assert list(df["open"]) == [1715.18, 1700.00]
    assert list(df["volume"]) == [2031608.0, 1500000.0]
    assert df["close"].dtype == "float64"


def test_time_becomes_sorted_index(monkeypatch):
    _patch_get(monkeypatch, _ok_payload())
    df = StockApiSource(token="TK").fetch_daily("600519", "20240102", "20240103")
    assert df.index[0] == pd.Timestamp("2024-01-02")
    assert df.index[1] == pd.Timestamp("2024-01-03")
    assert df.index.is_monotonic_increasing


def test_request_params_formatted_correctly(monkeypatch):
    captured = {}
    _patch_get(monkeypatch, _ok_payload(), captured)
    StockApiSource(token="TK").fetch_daily("600519", "20240102", "20240110")
    p = captured["params"]
    assert p["code"] == "600519"
    assert p["startDate"] == "2024-01-02"   # YYYYMMDD -> YYYY-MM-DD
    assert p["endDate"] == "2024-01-10"
    assert p["calculationCycle"] == "100"   # 日线必填
    assert p["token"] == "TK"


def test_token_read_from_env(monkeypatch):
    monkeypatch.setenv("STOCKAPI_TOKEN", "ENVTK")
    captured = {}
    _patch_get(monkeypatch, _ok_payload(), captured)
    StockApiSource().fetch_daily("600519", "20240102", "20240103")
    assert captured["params"]["token"] == "ENVTK"


def test_missing_token_raises(monkeypatch):
    monkeypatch.delenv("STOCKAPI_TOKEN", raising=False)
    with pytest.raises(ValueError, match="STOCKAPI_TOKEN"):
        StockApiSource().fetch_daily("600519", "20240102", "20240103")


def test_api_error_code_raises(monkeypatch):
    _patch_get(monkeypatch, {"msg": "fail", "code": 40001, "data": None})
    with pytest.raises(RuntimeError, match="40001"):
        StockApiSource(token="TK").fetch_daily("600519", "20240102", "20240103")


def test_empty_data_returns_empty_df(monkeypatch):
    _patch_get(monkeypatch, {"msg": "success", "code": 20000, "data": []})
    df = StockApiSource(token="TK").fetch_daily("600519", "20240102", "20240103")
    assert len(df) == 0
    assert df.index.name == "date"
