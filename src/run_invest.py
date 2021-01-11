import os
from src.binance_communication.ticker_streamer import TickerStreamer
from src.binance_communication.order_manager import OrderManager
from src.utils.trading_utils import round_decimals_down
import time
import asyncio


class RunInvest:

    def __init__(self, api_key, api_secret, market):
        self.ts = TickerStreamer(api_key, api_secret, market)
        self.op = OrderManager(api_key, api_secret)
        self.ts.start_stream(market)
        self.loop = asyncio.get_event_loop()
        self.market = market
        self.current_stop_price = 0
        self.min_time_between_orders = 0
        self.safety_margin = 5
        self.last_order = {}
        self.is_running = True
        self.is_selling = True

        del api_key
        del api_secret

    def run(self):
        print('Running...')
        time_start = time.time()
        time_passed = 0
        while self.is_running:

            # Check if selling or buying
            self.update_market_side()

            if self.is_selling:
                # If stop price is updated. Cancel previous stop limit order and file new order
                if self.ts.accountant.stop_price > self.current_stop_price and time_passed > self.min_time_between_orders:
                    # Update order
                    self.update_stop_limit_order_sell()
                    self.min_time_between_orders = 100
                    time_start = time.time()
            else:
                if self.last_order['status'] == 'FILLED' and not self.op.last_order_side == 'BUY':
                    last_price = float(self.last_order['price'])
                    # if (self.ts.accountant.ask_price > last_price + 5) or \
                    #         (self.ts.accountant.ask_price < last_price - self.ts.accountant.offset*2):
                    if self.ts.accountant.ask_price > last_price + self.safety_margin:
                        print('Execute market buy order...')
                        # Execute buy order
                        self.loop.run_until_complete(self.op.place_market_order(self.market,
                                                                                self.ts.client.SIDE_BUY,
                                                                                self.ts.accountant.tether_balance))
                        time.sleep(1)
                        # Reset stop price
                        print('Resetting prices...')
                        self.current_stop_price = round_decimals_down(self.current_stop_price / 2, 2)
                        self.ts.accountant.stop_price = round_decimals_down(last_price / 2, 2)
                        self.ts.accountant.limit_price = round_decimals_down(self.ts.accountant.stop_price - 0.25, 2)
                        self.min_time_between_orders = 5
                        self.safety_margin = 5
                        time_start = time.time()

                    if self.ts.accountant.ask_price - last_price - self.safety_margin < -10:
                        self.safety_margin -= 5
                        print(f'New buy price is: {last_price + self.safety_margin}')

            # Update time stamps
            time_end = time.time()
            time_passed = time_end - time_start

    def update_stop_limit_order_sell(self):
        # 1. Cancel previous order if one has been put
        if not self.op.last_order_market == '' and not self.op.last_order_side == 'BUY':
            print('Cancelling previous order...')
            cancel_ticket = self.loop.run_until_complete(self.op.cancel_order(self.op.last_order_market,
                                                                              self.op.last_order_id))
        time.sleep(1)
        print('Placing new order...')
        # 2. Place order
        order, placed_successful = self.loop.run_until_complete(self.op.place_order(self.market,
                                                                                    self.ts.client.SIDE_SELL,
                                                                                    self.ts.accountant.eth_balance,
                                                                                    self.ts.accountant.stop_price,
                                                                                    self.ts.accountant.limit_price))
        time.sleep(5)
        print(f'Stop limit order was placed: {placed_successful}')
        print(order)
        # 3. Update current stop price
        # print('Updating stop price...')
        self.current_stop_price = self.ts.accountant.stop_price

    def update_stop_limit_order_buy(self, stop_price, limit_price):
        # Create new stop limit order to execute if price rises again
        print('Creating buy order...')
        base_quantity = self.op.compute_max_buy(self.ts.accountant.tether_balance,
                                                limit_price,
                                                self.ts.market.step_size)

        order, placed_successful = self.loop.run_until_complete(self.op.place_order(self.market,
                                                                                    self.ts.client.SIDE_BUY,
                                                                                    base_quantity,
                                                                                    stop_price,
                                                                                    limit_price))
        time.sleep(1)
        print(f'Buy order placed successfully: {placed_successful}')
        print(order)

    def update_market_side(self):
        """Update market side by checking whether the last order has been filled or is open. If open this means that
           that there has been no change since last check. If the order is filled then we switch sides. """
        if self.op.last_order_id == 0:
            return

        # Check if orders have gone through
        self.last_order = self.loop.run_until_complete(self.op.get_order(self.market, self.op.last_order_id))

        if self.last_order['status'] == 'FILLED' and self.last_order['side'] == 'BUY':
            self.is_selling = True
            self.ts.set_balances()
        elif self.last_order['status'] == 'FILLED' and self.last_order['side'] == 'SELL':
            self.is_selling = False
            self.ts.set_balances()


if __name__ == '__main__':
    secret = os.environ.get('api_secret_common')
    key = os.environ.get('api_key_common')
    trade = 'ETHUSDT'

    run_invest = RunInvest(key, secret, trade)
    run_invest.run()
