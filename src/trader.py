from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from xtquant import xtconstant

from src.logger import setup_logger

logger = setup_logger(__name__)


class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        """
        连接断开
        :return:
        """
        logger.info("connection lost")

    def on_stock_order(self, order):
        """
        委托回报推送
        :param order: XtOrder对象
        :return:
        """
        logger.info("on order callback:")
        logger.info(order.stock_code, order.order_status, order.order_sysid)

    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        logger.info("on trade callback")
        logger.info(trade.account_id, trade.stock_code, trade.order_id)

    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        logger.error("on order_error callback")
        logger.error(order_error.order_id, order_error.error_id, order_error.error_msg)

    def on_cancel_error(self, cancel_error):
        """
        撤单失败推送
        :param cancel_error: XtCancelError 对象
        :return:
        """
        logger.error("on cancel_error callback")
        logger.error(
            cancel_error.order_id, cancel_error.error_id, cancel_error.error_msg
        )

    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        logger.info("on_order_stock_async_response")
        logger.info(response.account_id, response.order_id, response.seq)

    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        logger.info("on_account_status")
        logger.info(status.account_id, status.account_type, status.status)
