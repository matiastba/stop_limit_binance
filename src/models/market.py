

class Market:

    def __init__(self, symbol, base_asset, base_precision, quote_asset, quote_precision):
        self.symbol = symbol
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.base_precision = base_precision
        self.quote_precision = quote_precision
        self.step_size = 0
