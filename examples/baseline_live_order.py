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
# TODAY = "2026-03-12"
MONEY_PER_STOCK = 25000


def add_last_close_column(df: pd.DataFrame):
    unadj_price_df = pd.read_parquet(
        rf"D:\data_warehouse\vendor_clean_data\bar\1day\tushare\{TODAY}.parquet"
    ).set_index(["datetime", "symbol"])

    df["last_close"] = unadj_price_df.reindex(df[["datetime", "symbol"]])[
        "close"
    ].values
    return df


def get_target_positions():

    target_positions = pd.read_parquet(
        r"D:\model_data_warehouse\china_all\baseline_xgb5d_live\oof_select.parquet",
        filters=[("datetime", "==", pd.Timestamp(TODAY))],
    )
    target_positions = add_last_close_column(target_positions)
    target_positions["quantity"] = (
        (MONEY_PER_STOCK / target_positions["last_close"]).astype(int).round(-2)
    )
    target_positions["target_amount"] = (
        target_positions["quantity"] * target_positions["last_close"]
    )
    return target_positions


if __name__ == "__main__":
    logger.info(f"Today is {TODAY}")

    # ------------------------------------------------------------------------------------------
    # Position Session
    target_positions = get_target_positions()
    assert target_positions["datetime"].nunique() == 1, "Only one datetime is allowed"
    assert target_positions["datetime"].min() == pd.Timestamp(TODAY), (
        "The target position is not updated today"
    )
    # ------------------------------------------------------------------------------------------
    # Account Session

    # load env
    path = os.getenv("QMT_MINI_PATH")
    account_id = os.getenv("ACCOUNT_ID")

    # session_id为会话编号，策略使用方对于不同的Python策略需要使用不同的会话编号
    session_id = 111111
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
    positions_df["datetime"] = pd.Timestamp(TODAY)
    positions_df["weight"] = (
        (positions_df["market_value"] / positions_df["market_value"].sum())
        .mul(100)
        .round(2)
    )
    if positions:
        logger.info("Current Position is \n" + positions_df.to_string(index=False))

    # ------------------------------------------------------------------------------------------
    # Derive Orders
    # 1. If current position not in target position, sell it
    sell_names = positions_df[
        ~positions_df["stock_code"].isin(target_positions["symbol"])
    ]["stock_code"].to_list()
    sell_orders = positions_df.loc[
        positions_df["stock_code"].isin(sell_names),
        ["datetime", "stock_code", "volume"],
    ].rename(columns={"stock_code": "symbol", "volume": "quantity"})
    sell_orders["quantity"] = -sell_orders["quantity"]
    sell_orders["direction"] = "SELL"
    sell_orders = sell_orders.loc[sell_orders["quantity"] != 0]

    # 2. If target position not in current position, buy it
    buy_names = target_positions[
        ~target_positions["symbol"].isin(positions_df["stock_code"])
    ]["symbol"].to_list()
    buy_orders = target_positions.loc[
        target_positions["symbol"].isin(buy_names), ["datetime", "symbol", "quantity"]
    ]
    buy_orders["direction"] = "BUY"

    # 3. Agg all orders
    orders = pd.concat([sell_orders, buy_orders], axis=0)
    orders = add_last_close_column(orders)
    orders["amount"] = orders["quantity"] * orders["last_close"]

    # 4. Save orders
    logger.info("Orders are \n" + orders.to_string(index=False))
    orders.to_csv(
        rf"D:\data_warehouse\strategy_live\baseline\orders_{TODAY}.csv", index=False
    )

    # Stats
    logger.info(
        f"Total orders: {len(orders)}, sell: {len(sell_orders)}, buy: {len(buy_orders)}"
    )
    logger.info("\n" + orders.groupby("direction")["amount"].sum().to_string())
