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
    # Queies

    # query asset
    logger.info("Query asset:")
    asset = xt_trader.query_stock_asset(acc)
    if asset:
        logger.info(
            f"cash: {asset.cash:.2f}, market value: {asset.market_value:.2f}, total asset: {asset.total_asset:.2f}"
        )

    # query all orders for the day
    logger.info("Query all orders for the day:")
    orders = xt_trader.query_stock_orders(acc)
    logger.info(f"Number of orders = {len(orders)}")
    if orders:
        logger.info(f"last orders: {orders[-1]}")

    # query all trades for the day
    logger.info("Query all trades for the day:")
    trades = xt_trader.query_stock_trades(acc)
    logger.info(f"Number of trades = {len(trades)}")
    if trades:
        logger.info(f"last trades: {trades[-1]}")

    # query all positions
    logger.info("Query all positions:")
    positions = xt_trader.query_stock_positions(acc)
    logger.info(f"Number of positions = {len(positions)}")
    if positions:
        logger.info(
            f"last positions: code = {positions[-1].stock_code}, volume = {positions[-1].volume}, market_value = {positions[-1].market_value:.2f}"
        )
