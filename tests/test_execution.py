from ashare_pilot.execution import PaperBroker


def test_buy_reduces_cash_and_adds_position():
    broker = PaperBroker(cash=1000.0)
    broker.buy("000001", shares=100, price=8.0)
    assert broker.cash == 200.0
    assert broker.position("000001") == 100


def test_cannot_buy_without_enough_cash():
    broker = PaperBroker(cash=500.0)
    try:
        broker.buy("000001", shares=100, price=8.0)  # 需 800
        assert False, "资金不足应抛错"
    except ValueError:
        pass
    assert broker.position("000001") == 0


def test_sell_increases_cash_and_reduces_position():
    broker = PaperBroker(cash=1000.0)
    broker.buy("000001", shares=100, price=8.0)
    broker.sell("000001", shares=100, price=10.0)
    assert broker.cash == 1200.0
    assert broker.position("000001") == 0


def test_cannot_sell_more_than_held():
    broker = PaperBroker(cash=1000.0)
    broker.buy("000001", shares=100, price=8.0)
    try:
        broker.sell("000001", shares=200, price=10.0)
        assert False, "持仓不足应抛错"
    except ValueError:
        pass


def test_records_orders():
    broker = PaperBroker(cash=1000.0)
    broker.buy("000001", shares=50, price=8.0)
    broker.sell("000001", shares=50, price=9.0)
    assert len(broker.orders) == 2
    assert broker.orders[0].side == "buy"
    assert broker.orders[1].side == "sell"
