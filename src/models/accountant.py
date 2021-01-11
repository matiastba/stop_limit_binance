

class Accountant:

    def __init__(self):
        self.tether_balance = 0
        self.eth_balance = 0
        self.bid_price = 0
        self.ask_price = 0
        self.stop_price = 0
        self.limit_price = 0
        self.offset = 10

    def set_tether_balance(self, balance):
        self.tether_balance = balance

    def set_eth_balance(self, balance):
        self.eth_balance = balance

    def update_prices(self, bid_price, ask_price):
        self.bid_price = bid_price
        self.ask_price = ask_price

        if self.bid_price - self.offset > self.stop_price:
            self.stop_price = self.bid_price - self.offset
            self.limit_price = self.stop_price - 0.25
