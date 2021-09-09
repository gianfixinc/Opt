from Opt.american_option_pricing import AmericanOptionPricing
from Opt.base_option_pricing import OptionPricingBase
from Opt.data_fetcher import *

if __name__ == '__main__':
    pricer = AmericanOptionPricing('PFE', datetime.datetime(2021, 9, 24), 47)
    call, put = pricer.calculate_option_prices()
    parity = pricer.is_call_put_parity_maintained(call, put)
    print(f"Parity = {parity}")