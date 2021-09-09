import datetime
import pandas as pd
import quandl
from loguru import logger as log
from pandas.tseries.offsets import BDay
from pandas_datareader import data

quandl.ApiConfig.api_key = 'PzR-SwKHZm7Axanmyjm9'

SOURCES = ['yahoo', 'morningstar']


def get_ranged_data(ticker: float, start: datetime.date, end=None, useQuandl=True):
    if not end:
        end = datetime.date.today()
    df = pd.DataFrame()
    if useQuandl:
        log.info(f"Fetching data for Ticker={ticker} from Source=Quandl")
        df = quandl.get("WIKI/" + ticker, start_date=start, end_date=end)
        log.info("### Successfully fetched data!!")
    else:
        for source in SOURCES:
            try:
                log.info(f"Fetching data for Ticker={ticker} from Source={source}")
                df = data.DataReader(ticker, source, start, end)
                if not df.empty:
                    log.info("### Successfully fetched data!!")
                    break
            except Exception as exception:
                log.warn(f"Received exception from Source={source} for Ticker={ticker}")
                log.warn(str(exception))
    return df


def get_data(ticker: float, useQuandl=True):
    df = pd.DataFrame()
    if useQuandl:
        log.info(f"Fetching data for Ticker={ticker} from Source=Quandl")
        df = quandl.get("WIKI/" + ticker)
        log.info("### Successfully fetched data!!")
    else:
        for source in SOURCES:
            try:
                log.info(f"Fetching data for Ticker={ticker} from Source={source}")
                df = data.DataReader(ticker, source)
                if not df.empty:
                    log.info("### Successfully fetched data!!")
                    break
            except Exception as exception:
                log.warn(f"Received exception from Source={source} for Ticker={ticker}")
                log.warn(str(exception))
    return df


def get_treasury_rate(ticker=None):
    df = pd.DataFrame()
    if not ticker:
        ticker = 'DTB3'  # Default to 3-Month Treasury Rate
    prev_business_date = datetime.datetime.today() - BDay(1)
    log.info(f"Fetching data for Ticker={ticker} from Source=Quandl")
    df = quandl.get("FRED/" + ticker, start_date=prev_business_date - BDay(2), end_date=prev_business_date - BDay(1))
    if df.empty:
        log.error("Unable to get Treasury Rates from Quandl. Please check connection")
        raise IOError("Unable to get Treasury Rate from Quandl")
    log.info("### Successfully fetched data!!")
    print(df['Value'][0])
    return df['Value'][0]


def get_spx_prices(start_date=None):
    if not start_date:
        start_date = datetime.datetime(2017, 1, 1)
    df = pd.DataFrame()
    df = get_data('SPX', start_date, useQuandl=False)
    if df.empty:
        log.error("Unable to get SNP 500 Index from Web. Please check connection")
        raise IOError("Unable to get SPX from Web")
    return df
