import os

from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from xtquant import xtconstant

from src.logger import logger
from src.trader import MyXtQuantTraderCallback

from dotenv import load_dotenv

# Load the .env
load_dotenv()

if __name__ == "__main__":
    logger.info("q-trader test")

    # load env
    path = os.getenv("QMT_MINI_PATH")
    account_id = os.getenv("ACCOUNT_ID")

    # session_id为会话编号，策略使用方对于不同的Python策略需要使用不同的会话编号
    session_id = 123456
    xt_trader = XtQuantTrader(path, session_id)
    acc = StockAccount(account_id, "STOCK")
    callback = MyXtQuantTraderCallback()
    xt_trader.register_callback(callback)

    # Start trading session
    xt_trader.start()
    connect_result = xt_trader.connect()
    logger.info(f"connect_result (0 means success): {connect_result}")
    subscribe_result = xt_trader.subscribe(acc)
    logger.info(f"subscribe_result (0 means success): {subscribe_result}")

    # ------------------------------------------------------------------------------------------
    # Orders
    # Place order

    stock_code = "600000.SH"
    logger.info(f"Placing order for {stock_code} using the fix price:")
    order_id = xt_trader.order_stock(
        account=acc,
        stock_code=stock_code,
        order_type=xtconstant.STOCK_BUY,
        order_volume=100,
        price_type=xtconstant.FIX_PRICE,
        price=9.2,
        strategy_name="test_strategy",
        order_remark="test_remark",
    )
    logger.info(f"order_id: {order_id}")

    # Cancel order
    logger.info(f"Canceling order for {order_id}:")
    cancel_result = xt_trader.cancel_order_stock(
        account=acc,
        order_id=order_id,
    )
    logger.info(f"cancel_result (0 means success): {cancel_result}")

    # # Place order async
    # logger.info(f"Placing async order for {stock_code} using the fix price:")
    # async_seq = xt_trader.order_stock_async(
    #     account=acc,
    #     stock_code=stock_code,
    #     order_type=xtconstant.STOCK_BUY,
    #     order_volume=100,
    #     price_type=xtconstant.FIX_PRICE,
    #     price=9.2,
    #     strategy_name="test_strategy",
    #     order_remark="test_remark",
    # )
    # logger.info(f"async_seq: {async_seq}")

    # # query order
    # logger.info(f"Query order for {order_id}:")
    # order = xt_trader.query_order_stock(acc, order_id)
    # if order:
    #     logger.info(f"order: {order}")
    #     logger.info(f"order_status: {order.order_status}")

    # # query position with stock_code
    # logger.info(f"Query position for {stock_code}:")
    # position = xt_trader.query_stock_position(acc, stock_code)
    # if position:
    #     logger.info(f"position: {position}")
