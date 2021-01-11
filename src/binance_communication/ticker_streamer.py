from binance.client import Client
from binance.websockets import BinanceSocketManager
from twisted.internet import reactor
from src.models.accountant import Accountant
from src.models.market import Market
from src.utils.trading_utils import round_decimals_down
import numpy as np
import os


class TickerStreamer:

    def __init__(self, api_key, api_secret, symbol):

        self.client = Client(api_key, api_secret)
        self.accountant = Accountant()

        self.market_info = self.client.get_symbol_info(symbol)
        self.market = Market(self.market_info['symbol'],
                             self.market_info['baseAsset'],
                             int(self.market_info['baseAssetPrecision']),
                             self.market_info['quoteAsset'],
                             int(self.market_info['quoteAssetPrecision']))
        self.set_market_precision()
        self.set_balances()
        # ----- Delete keys from memory -----
        del api_key
        del api_secret

    def get_client_asset_balance(self, asset):
        return float(self.client.get_asset_balance(asset=asset)['free'])

    def get_client_binance_coin_balance(self):
        return float(self.client.get_asset_balance(asset='BNB')['free'])

    def set_balances(self):
        self.accountant.tether_balance = round_decimals_down(self.get_client_asset_balance('USDT'), self.market.step_size)
        self.accountant.eth_balance = round_decimals_down(self.get_client_asset_balance('ETH'), self.market.step_size)

    def set_market_precision(self):
        self.market.step_size = int(-1*np.log10(float(self.market_info['filters'][2]['stepSize'])))

    def start_stream(self, market):
        # ----- Start stream. Will run until stop_stream() is called -----
        bm = BinanceSocketManager(self.client)
        _ = bm.start_symbol_book_ticker_socket(market, self._update_prices)
        bm.start()

    def _update_prices(self, market_status):
        self.accountant.update_prices(float(market_status['b']), float(market_status['a']))

    @staticmethod
    def stop_stream():
        # ----- Stop stream -----
        reactor.stop()

    @staticmethod
    def _get_precision(market):
        # ----- Get precisions for base and quote assets -----

        base_precision = int(market["baseAssetPrecision"])
        quote_precision = int(market["quotePrecision"])

        return [base_precision, quote_precision]


if __name__ == '__main__':
    secret = os.environ.get('api_secret')
    key = os.environ.get('api_key')
    trade = 'ETHUSDT'

    ts = TickerStreamer(key, secret)
    ts.start_stream(trade)
