import datetime
import logging
import numpy as np
from random import gauss
from loguru import logger as log
from Opt.base_option_pricing import OptionPricingBase


class AmericanOptionPricing(OptionPricingBase):
    """
    This class uses Monte-Carlo simulation to calculate prices for American Call and Put Options.
    """
    SIMULATION_COUNT = 200000  # Number of Simulations to be performed for Brownian motion

    def __init__(self, ticker: str, expiry_date: datetime.date, strike: float, dividend=0.0):
        super(AmericanOptionPricing, self).__init__(ticker, expiry_date, strike, dividend=dividend)
        log.info("American Option Pricing. Initializing variables")

        # Get/Calculate all the required underlying parameters, ex. Volatility, Risk-free rate, etc.
        self.initialize_variables()
        self.log_parameters()

    def _generate_asset_price(self):
        """ Calculate predicted Asset Price at the time of Option Expiry date.
        It used a random variable based on Gaus model and then calculate price using the below equation.
            St = S * exp((r− 0.5*σ^2)(T−t)+σT−t√ϵ)
        :return: <float> Expected Asset Price
        """
        expected_price = self.spot_price * np.exp(
            (self.risk_free_rate - 0.5 * self.volatility ** 2) * self.time_to_maturity +
            self.volatility * np.sqrt(self.time_to_maturity) * gauss(0.0, 1.0))
        # log.debug("expected price %f " % expected_price)
        return expected_price

    def _call_payoff(self, expected_price: float):
        """ Calculate payoff of the call option at Option Expiry Date assuming the asset price
        is equal to expected price. This calculation is based on below equation:
            Payoff at T = max(0,ExpectedPrice−Strike)
        :param expected_price: <float> Expected price of the underlying asset on Expiry Date
        :return: <float> payoff
        """
        return max(0, expected_price - self.strike_price)

    def _put_payoff(self, expected_price: float):
        """ Calculate payoff of the put option at Option Expiry Date assuming the asset price
        is equal to expected price. This calculation is based on below equation:
            Payoff at T = max(0,Strike-ExpectedPrice)
        :param expected_price: <float> Expected price of the underlying asset on Expiry Date
        :return: <float> payoff
        """
        return max(0, self.strike_price - expected_price)

    def _generate_simulations(self):
        """ Perform Brownian motion simulation to get the Call & Put option payouts on Expiry Date
        :return: <list of call-option payoffs>, <list of put-option payoffs>
        """
        call_payoffs, put_payoffs = [], []
        for _ in range(self.SIMULATION_COUNT):
            expected_asset_price = self._generate_asset_price()
            call_payoffs.append(self._call_payoff(expected_asset_price))
            put_payoffs.append(self._put_payoff(expected_asset_price))
        return call_payoffs, put_payoffs

    def calculate_option_prices(self):
        """ Calculate present-value of of expected payoffs and their average becomes the price of the respective option.
        Calculations are performed based on below equations:
            Ct=PV(E[max(0,PriceAtExpiry−Strike)])
            Pt=PV(E[max(0,Strike−PriceAtExpiry)])
        Assumption: risk free rate == 0 --> after long analysis is the real risk free rate for Dev Countries
        :return: <float>, <float> Calculated price of Call & Put options
        """
        call_payoffs, put_payoffs = self._generate_simulations()
        discount_factor = np.exp(-1 * 0.0002500 * self.time_to_maturity) #* self.risk_free_rate
        call_price = discount_factor * (sum(call_payoffs) / len(call_payoffs))
        put_price = discount_factor * (sum(put_payoffs) / len(put_payoffs))
        log.info("### Call Price calculated at %f " % call_price)
        log.info("### Put Price calculated at %f " % put_price)
        return call_price, put_price


if __name__ == '__main__':
    pricer = AmericanOptionPricing('AAPL', datetime.datetime(2021, 9, 24), 165)
    call, put = pricer.calculate_option_prices()
    parity = pricer.is_call_put_parity_maintained(call, put)
    print(f"Parity = {parity}")