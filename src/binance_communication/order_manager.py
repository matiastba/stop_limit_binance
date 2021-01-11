from binance.client import Client
from binance.exceptions import BinanceAPIException as BAE, BinanceOrderException as BOE, BinanceRequestException as BRE
from src.utils.trading_utils import round_decimals_down
import os
import time
import win32api
import asyncio


class OrderManager:

    def __init__(self, api_key, api_secret):
        self._client = Client(api_key, api_secret)
        self.last_order_id = 0
        self.last_order_market = ''
        self.last_order_side = ''
        self._set_system_time()

        del api_key
        del api_secret

    async def place_order(self, symbol, side, quantity, stop_price, limit_price):
        """Method used to place orders.
        INPUTS:
                symbol:   String with market symbol for which to place order. (E.g. 'BNBBTC')
                side:     String indicating if it is a BUY or SELL order.
                quantity: Float quantity to BUY or SELL of quote or base asset respectively.
        OUTPUTS:
                order/exception: Dict. Order info if order was successful / Error info if not successful.
                success:         Boolean indicating whether order was successful (True) or not (False).
        """
        async def _place_order():
            if side == 'BUY':
                return self._client.create_order(symbol=symbol,
                                                 side=side,
                                                 type=self._client.ORDER_TYPE_STOP_LOSS_LIMIT,
                                                 quantity=quantity,
                                                 stopPrice=stop_price,
                                                 timeInForce=self._client.TIME_IN_FORCE_GTC,
                                                 price=limit_price)
            if side == 'SELL':
                return self._client.create_order(symbol=symbol,
                                                 side=side,
                                                 type=self._client.ORDER_TYPE_STOP_LOSS_LIMIT,
                                                 quantity=quantity,
                                                 stopPrice=stop_price,
                                                 timeInForce=self._client.TIME_IN_FORCE_GTC,
                                                 price=limit_price)
        order = {}
        try:
            order = await _place_order()
            self.last_order_id = order['orderId']
            self.last_order_market = order['symbol']
            self.last_order_side = side
            success = True
            return order, success
        except (BOE, BAE, BRE) as e:
            success = False
            return e, success

    async def place_market_order(self, symbol, side, quantity):
        """Method used to place orders.
        INPUTS:
                symbol:   String with market symbol for which to place order. (E.g. 'BNBBTC')
                side:     String indicating if it is a BUY or SELL order.
                quantity: Float quantity to BUY or SELL of quote or base asset respectively.
        OUTPUTS:
                order/exception: Dict. Order info if order was successful / Error info if not successful.
                success:         Boolean indicating whether order was successful (True) or not (False).
        """

        async def _place_market_order():
            """Method starting the order request towards Binance.
            OUTPUTS:
                    order/exception: Dict. Order info if order was successful / Error info if not successful.
                    success:         Boolean indicating whether order was successful (True) or not (False)."""
            if side == 'BUY':
                return self._client.create_order(symbol=symbol,
                                                 side=side,
                                                 type=self._client.ORDER_TYPE_MARKET,
                                                 quoteOrderQty=quantity)
            if side == 'SELL':
                return self._client.create_order(symbol=symbol,
                                                 side=side,
                                                 type=self._client.ORDER_TYPE_MARKET,
                                                 quantity=quantity)

        try:
            order = await _place_market_order()
            self.last_order_id = order['orderId']
            self.last_order_market = order['symbol']
            self.last_order_side = side
            success = True
            return order, success
        except (BOE, BAE, BRE) as e:
            success = False
            return e, success

    def compute_max_buy(self, asset_balance, market_price, precision):
        """Compute largest amount possible to buy with current asset balance and market price. If no balance
           is available max_buy=None. If the request was not handled within timeout an exception will be raised."""
        max_buy = round_decimals_down(asset_balance/market_price, precision)
        return max_buy

    def get_open_orders(self, market):
        return self._client.get_open_orders(symbol=market)

    async def get_order(self, market, order_id, valid_time=10000):
        async def _get_order():
            return self._client.get_order(symbol=market, orderId=order_id, recvWindow=valid_time)
        order = await _get_order()
        return order

    async def cancel_order(self, market, order_id):
        async def _cancel_order():
            return self._client.cancel_order(symbol=market, orderId=order_id)
        cancel_ticket = await _cancel_order()
        self.last_order_id = 0
        self.last_order_market = ''
        return cancel_ticket

    def _set_system_time(self):
        gt = self._client.get_server_time()
        tt = time.gmtime(int((gt["serverTime"]) / 1000))
        win32api.SetSystemTime(tt[0], tt[1], 0, tt[2], tt[3], tt[4], tt[5], 0)


if __name__ == '__main__':
    secret = os.environ.get('api_secret_common')
    key = os.environ.get('api_key_common')
    trade = 'ETHUSDT'

    loop = asyncio.get_event_loop()
    om = OrderManager(key, secret)
    max_quantity = 0.00826 #om.compute_max_buy(10.4, 1101, 5)

    order_ticket, success = loop.run_until_complete(om.place_order(trade, 'BUY', max_quantity, 1240, 1241))
    print(order_ticket)
    orderId = order_ticket['orderId']
    time.sleep(10)
    ticket = om.cancel_order(trade, orderId)
    print(ticket)
