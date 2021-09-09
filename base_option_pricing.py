import datetime
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
from loguru import logger as log
from Opt.data_fetcher import get_ranged_data, get_treasury_rate


class OptionPricingBase(object):
    LOOK_BACK_WINDOW = 252

    def __init__(self, ticker: str, expiry_date: datetime.date, strike: float, dividend=0.0):
        """
        :param ticker: Ticker of the Underlying Stock asset, ex. 'AAPL', 'TSLA', 'GOOGL', etc.
        :param expiry_date: <datetime.date> ExpiryDate for the option -must be in the future
        :param strike: <float> Strike price of the option. This is the price option holder plans to
        buy underlying asset (for call option) or sell underlying asset (for put option).
        :param dividend: <float> If the underlying asset is paying dividend to stock-holders.
        """
        self.ticker = ticker
        self.expiry = expiry_date
        self.strike_price = strike
        self.volatility = None  # We will calculate this based on historical asset prices
        self.time_to_maturity = None  # Calculated from expiry date of the option
        self.risk_free_rate = None  # We will fetch current 3-month Treasury rate from the web
        self.spot_price = None  # We will fetch latest stock price of the underlying asset from the web
        self.dividend = dividend or 0.0
        self.__underlying_asset_data = pd.DataFrame()  # Placeholder for underlying stock prices
        self.__start_date = datetime.datetime.today() - BDay(self.LOOK_BACK_WINDOW)  # How far we need to go
        # to get historical prices

    def initialize_variables(self):
        """
        Initialize all the required parameters for Option pricing
        :return:
        """
        log.debug("initializing variables started")
        self._set_risk_free_rate()
        self._set_time_to_maturity()
        self._set_volatility()
        self._set_spot_price()
        log.debug("initializing variables completed")

    def _set_risk_free_rate(self):
        """
        Fetch 3-month Treasury Bill Rate from the web. Please check module stock_analyzer.data_fetcher for details
        :return: <void>
        """
        log.info("Fetching Risk Free Rate")
        self.risk_free_rate = get_treasury_rate()
        log.info(f"Risk Free Rate = {self.risk_free_rate}")

    def _set_time_to_maturity(self):
        """
        Calculate TimeToMaturity in Years. It is calculated in terms of years using below formula,
            (ExpiryDate - CurrentDate).days / 365
        :return: <void>
        """
        if self.expiry < datetime.datetime.today():
            log.error("Expiry/Maturity Date is in the past. Please check...")
            raise ValueError("Expiry/Maturity Date is in the past. Please check...")
        self.time_to_maturity = (self.expiry - datetime.datetime.today()).days / 365.0
        log.info(f"Setting Time To Maturity to {self.time_to_maturity} days as Expiry/Maturity Date provided is {self.expiry}")

    def override_historical_start_date(self, hist_start_date):
        """
        If we want to change the look_back window for historical prices (used for volatility calculations),
        we can override the look_back window here. Farther back the start date is bigger our window.
        :param hist_start_date:
        :return: <void>
        """
        self.__start_date = hist_start_date

    def _get_underlying_asset_data(self):
        """
        Scan through the web to get historical prices of the underlying asset.
        Please check module stock_analyzer.data_fetcher for details
        :return:
        """
        if self.__underlying_asset_data.empty:
            log.info(
                f"Getting historical stock data for {self.ticker}; used to calculate volatility in this asset")
            self.__underlying_asset_data = get_ranged_data(self.ticker, self.__start_date, None, useQuandl=False)
            if self.__underlying_asset_data.empty:
                log.error("Unable to get historical stock data")
                raise IOError(f"Unable to get historical stock data for {self.ticker}!!")

    def _set_volatility(self):
        """
        Using historical prices of the underlying asset, calculate volatility.
        :return:
        """
        self._get_underlying_asset_data()
        self.__underlying_asset_data.reset_index(inplace=True)
        self.__underlying_asset_data.set_index("Date", inplace=True)
        log.debug("# now calculating log returns")
        self.__underlying_asset_data['log_returns'] = np.log(
            self.__underlying_asset_data['Close'] / self.__underlying_asset_data['Close'].shift(1))
        log.debug("# now calculating annualized volatility")
        d_std = np.std(self.__underlying_asset_data.log_returns)
        std = d_std * 252 ** 0.5
        log.info(f"# Annualized Volatility calculated is {std}")
        self.volatility = std

    def _set_spot_price(self):
        """
        Get latest price of the underlying asset.
        :return:
        """
        self._get_underlying_asset_data()
        print(self.__underlying_asset_data['Close'][-1])
        self.spot_price = self.__underlying_asset_data['Close'][-1]

    def log_parameters(self):
        """
        Useful method for logging purpose. Prints all the parameter values required for Option pricing.
        :return: <void>
        """
        log.info(f"### TICKER = {self.ticker}")
        log.info(f"### STRIKE = {self.strike_price}")
        log.info(f"### DIVIDEND = {self.dividend}")
        log.info(f"### VOLATILITY = {self.volatility}")
        log.info(f"### TIME TO MATURITY = {self.time_to_maturity}")
        log.info(f"### RISK FREE RATE = {self.risk_free_rate}")
        log.info(f"### SPOT PRICE = {self.spot_price}")

    def is_call_put_parity_maintained(self, call_price: float, put_price: float):
        """ Verify is the Put-Call Pairty is maintained by the two option prices calculated by us.
        :param call_price: <float>
        :param put_price: <float>
        :return: True, if Put-Call parity is maintained else False
        """
        lhs = call_price - put_price
        rhs = self.spot_price - np.exp(-1 * self.risk_free_rate * self.time_to_maturity) * self.strike_price
        log.info(f"Put-Call Parity LHS = {lhs}")
        log.info(f"Put-Call Parity RHS = {rhs}")
        return bool(round(lhs) == round(rhs))
