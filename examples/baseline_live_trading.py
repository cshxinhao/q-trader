# TODO: There should be a intraday live order panel, indicating the total orders placed, and its completion status
# TODO: Design an simple algo, with agressiveness parameter, the algo can place quotes or take liquidity, based on the market depth
# TODO: Set a time frame, for the order to be completed
# TODO: To monitor the market depth, indicating the deviation of order-price and current orderbook
# TODO: In order to achieve the above, the trader needs to subscribe / or frequently quote most updated market depth

import os
import pandas as pd
from dotenv import load_dotenv
from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from xtquant import xtconstant

from src.logger import setup_logger
from src.trader import MyXtQuantTraderCallback


# Load the .env
load_dotenv()

logger = setup_logger("Baseline Live")

# Config
TODAY = pd.Timestamp.today().strftime("%Y-%m-%d")
MODE = "BUY"  # 'BUY


def get_orders():
    trade_calendar = pd.read_parquet(
        r"D:\data_warehouse\vendor_clean_data\trade_calendar\tushare\trade_calendar.parquet",
        filters=[("calendar_date", ">=", pd.Timestamp("2026-01-01"))],
    ).set_index("calendar_date")

    if TODAY not in trade_calendar.index:
        prev_trade_date = trade_calendar.index[-1].strftime("%Y-%m-%d")
    else:
        prev_trade_date = trade_calendar.loc[TODAY, "pre_trade_date"].strftime(
            "%Y-%m-%d"
        )

    orders = pd.read_csv(
        rf"D:\data_warehouse\strategy_live\baseline\orders_{prev_trade_date}.csv",
        parse_dates=["datetime"],
    )
    return orders


def interact():
    import code

    code.InteractiveConsole(locals=globals()).interact()


if __name__ == "__main__":
    logger.info(f"Today is {TODAY}")

    # ------------------------------------------------------------------------------------------
    # Position Session
    orders = get_orders()

    # ------------------------------------------------------------------------------------------
    # Pre-trading Session

    # load env
    path = os.getenv("QMT_MINI_PATH")
    account_id = os.getenv("ACCOUNT_ID")

    # session_id为会话编号，策略使用方对于不同的Python策略需要使用不同的会话编号
    session_id = 666666
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

    # query all positions
    logger.info("Query all positions:")
    positions = xt_trader.query_stock_positions(acc)
    logger.info(f"Number of positions = {len(positions)}")
    positions_df = pd.DataFrame(
        [[pos.stock_code, pos.volume, pos.market_value] for pos in positions],
        columns=["stock_code", "volume", "market_value"],
    )
    positions_df["weight"] = (
        (positions_df["market_value"] / positions_df["market_value"].sum())
        .mul(100)
        .round(2)
    )
    if positions:
        logger.info("Current Position is \n" + positions_df.to_string(index=False))

    # ------------------------------------------------------------------------------------------
    # Trading Session

    if MODE == "SELL":
        # Sell first, to spare the cash
        sell_orders = orders.loc[orders["direction"] == "SELL"]
        for _, order in sell_orders.iterrows():
            stock_code = order["symbol"]
            order_type = xtconstant.STOCK_SELL if order["direction"] == "SELL" else None
            quantity = abs(order["quantity"])
            price_type = xtconstant.LATEST_PRICE
            price = 0

            # Check qty again
            if stock_code not in positions_df["stock_code"].values:
                logger.error(f"{stock_code} not in positions, might sold already!")
                continue
            pos_qty = positions_df.loc[
                positions_df["stock_code"] == stock_code, "volume"
            ].values[0]
            if pos_qty < quantity:
                logger.error(
                    f"Not enough qty to sell {stock_code}, might sold already!"
                )
                continue

            market_val = positions_df.loc[
                positions_df["stock_code"] == stock_code, "market_value"
            ].values[0]
            remark = f"SELL {stock_code} {quantity}@{price}, amount={market_val:.2f}"
            logger.info(remark)

            async_seq = xt_trader.order_stock_async(
                account=acc,
                stock_code=stock_code,
                order_type=order_type,
                order_volume=quantity,
                price_type=price_type,
                price=price,
                strategy_name="Baseline Live",
                order_remark=remark,
            )
            if async_seq == -1:
                logger.error("Order failed")
            else:
                logger.info("Order sent successfully")

    if MODE == "BUY":
        # Buy after
        buy_orders = orders.loc[orders["direction"] == "BUY"]
        for _, order in buy_orders.iterrows():
            stock_code = order["symbol"]
            order_type = xtconstant.STOCK_BUY if order["direction"] == "BUY" else None
            quantity = abs(order["quantity"])
            price_type = xtconstant.LATEST_PRICE
            price = 0

            # Check qty again
            if stock_code in positions_df["stock_code"].values:
                logger.error(
                    f"{stock_code} already in positions, might bought already!"
                )
                continue

            # # Check cash
            # asset = xt_trader.query_stock_asset(acc)
            # if asset.cash < :
            #     logger.error(
            #         f"Not enough cash to buy {stock_code}, amount={:.2f}"
            #     )
            #     continue

            # remark = f"BUY {stock_code} {quantity}@{price}, amount={:.2f}"
            # logger.info(remark)

            async_seq = xt_trader.order_stock_async(
                account=acc,
                stock_code=stock_code,
                order_type=order_type,
                order_volume=quantity,
                price_type=price_type,
                price=price,
                strategy_name="Baseline Live",
                order_remark="",
            )
            if async_seq == -1:
                logger.error("Order failed")
            else:
                logger.info("Order sent successfully")

    # ------------------------------------------------------------------------------------------
    # After Trading Session

    # query all orders for the day
    logger.info("Query all orders for the day:")
    orders = xt_trader.query_stock_orders(acc)
    logger.info(f"Number of orders = {len(orders)}")
    if orders:
        logger.info(f"last orders: {orders[-1].stock_code}")

    # query all trades for the day
    logger.info("Query all trades for the day:")
    trades = xt_trader.query_stock_trades(acc)
    logger.info(f"Number of trades = {len(trades)}")
    if trades:
        logger.info(f"last trades: {trades[-1]}")

    xt_trader.run_forever()
