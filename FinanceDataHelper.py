import yfinance as yf
import pandas as pd 
import datetime
import pandas_market_calendars as mcal

class FinanceDataHelper:
    @staticmethod
    def get_sp500_tickers() -> list:
        # Ref: https://stackoverflow.com/a/75845569/
        # url = 'https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx'
        #return_list = list(pd.read_excel(url, engine='openpyxl', index_col='Ticker', skiprows=4).dropna().index)
        url = 'https://en.m.wikipedia.org/wiki/List_of_S%26P_500_companies'
        return_list = list(pd.read_html(url, attrs={'id': 'constituents'}, index_col='Symbol')[0].index) #type: ignore
        if 'BRK.B' in return_list:
            return_list.remove('BRK.B')
            return_list.append('BRK-B')
        return return_list

    @staticmethod
    def get_business_days(start_date: datetime.date = (datetime.date.today() - datetime.timedelta(days=365)), days: int|None = None) -> list:
        nyse = mcal.get_calendar('NYSE')
        business_days = list(nyse.schedule(start_date=start_date, end_date=datetime.date.today()).index)
        return business_days if days is None else business_days[-days:]

    @staticmethod
    def get_minutely_data(symbol: str, business_days: list) -> pd.Series:
        # This is a list of tuples with start and end dates for each 5-day period
        start_and_ends = [(business_days[i], business_days[min(i+4,len(business_days)-1)]) for i in range(0, len(business_days), 5)]

        # Get all the data
        data_series = yf.download(tickers=symbol, start=start_and_ends[0][0], end=start_and_ends[0][1], period='5d', interval='1m')['Close']
        for i in range(1,len(start_and_ends)):
            data_series = pd.concat([data_series, yf.download(tickers=symbol, start=start_and_ends[i][0], end=(start_and_ends[i][1] + datetime.timedelta(days=1)), period='5d', interval='1m')['Close']])
        data_series.index = data_series.index.tz_localize(None) #type: ignore

        return data_series #type: ignore

    @staticmethod
    def get_stock_month_data(symbol: str, most_recent_day: bool = False) -> pd.DataFrame:
        # Get the end of the business days
        business_days = FinanceDataHelper.get_business_days(days=56)
        yf_series_months_daily = yf.download(tickers=symbol, start=business_days[0], end=(business_days[-1] + datetime.timedelta(days=1)), period='3mo', interval='1d')['Close']
        
        # Only collect minutely data from within the past month (all that is allowed)
        last_valid_idx = 0
        for i in range(len(business_days)-1, -1, -1):
            if business_days[i] <= (datetime.datetime.now() - datetime.timedelta(days=26)):
                last_valid_idx = i-1
                break
        recent_business_days = business_days[last_valid_idx:]

        yf_series_month_minutely = FinanceDataHelper.get_minutely_data(symbol, recent_business_days)

        base_idx = 0 if most_recent_day else 1

        df = None

        # If base_idx is 1, make it loop one less time
        for i in range(-(1+base_idx), -(len(recent_business_days)), -1):
            # Loop in reverse so that the (negative) index from recent_business_days is the same as business_days
            selected_date = business_days[i]
            # The next day
            selected_date_end = business_days[i].date() + datetime.timedelta(days=1)
            # The day after the next business day
            next_date_end = business_days[i+1].date() + datetime.timedelta(days=1) if i < -1 else None
            # About a month before
            date_30 = business_days[i-25].date()
            # 5 business days before
            date_5 = business_days[i-4].date()

            df = FinanceDataHelper.append_stock_data_to_df_with_input(yf_series_months_daily, yf_series_month_minutely, df, symbol, selected_date, date_30, date_5, selected_date_end, next_date_end)
            
        return df #type: ignore

    @staticmethod
    def append_stock_data_to_df_with_input(input_daily_series: pd.Series, input_minutely_series: pd.Series, output_df: pd.DataFrame|None, symbol: str, selected_date: str, date_30: str, date_5: str, end_date: str, next_date_end: str|None = None) -> pd.DataFrame: #type: ignore
        stock_dict: dict = {}
        rof_n: int = 9

        # This base index subtracts one if the next end date is included (i.e. we are getting the last day without any testing data)
        month_base_idx = 0 if next_date_end is None else -1

        try:
            # Get the correct range of the data we need
            max_date_exclusive = pd.Timestamp(end_date if next_date_end is None else next_date_end)
            daily_data = input_daily_series[input_daily_series.index < max_date_exclusive]
            minutely_data = input_minutely_series[input_minutely_series.index < (pd.Timestamp(selected_date) + datetime.timedelta(days=1))]

            stock_dict['RateOfChange'] = daily_data.iloc[-1+month_base_idx] / daily_data.iloc[-rof_n-1+month_base_idx]

            for i in range(1,15):
                # Ad month_base_idx because -1 is actually the next day if month_base_idx is -1
                stock_dict[f'{i}Day{"" if i == 1 else "sAgo"}ChangePercent'] = (daily_data.iloc[-i+month_base_idx] - daily_data.iloc[-(i+1)+month_base_idx]) / daily_data.iloc[-(i+1)+month_base_idx]
            for i in [1,5,30]:
                stock_dict[f'{i}MinChangePercent'] = (minutely_data.iloc[-1] - minutely_data.iloc[-(i+1)]) / minutely_data.iloc[-(i+1)]
            for i in [1,5,10]:
                stock_dict[f'{i}HourChangePercent'] = (minutely_data.iloc[-1] - minutely_data.iloc[-(i*60+1)]) / minutely_data.iloc[-(i*60+1)]
            stock_dict["NextDayChangePercent"] = None if next_date_end is None else (daily_data.iloc[-1] - daily_data.iloc[-2]) / daily_data.iloc[-2]

            new_append_df = pd.DataFrame(data=stock_dict, index=[None]).set_index(pd.MultiIndex.from_tuples([(symbol,selected_date)],names=["Symbol","Date"]))

            return new_append_df if output_df is None else pd.concat([output_df,new_append_df])
        except IndexError as e:
            print(f"Index error retrieving data for {symbol} stock on {selected_date}: {e}")
        except Exception as e:
            print(f"Error retrieving data for {symbol} stock on {selected_date}: {e}")


