import pandas as pd
from FinanceDataHelper import FinanceDataHelper

class FinanceData(object):
    @staticmethod
    def get_data(save_to_csv: bool = True, file_path_name: str | None = None, most_recent_day: bool = True) -> pd.DataFrame | None:
        if save_to_csv and file_path_name is None:
            raise ValueError('Must include a file path (including name) if saving to csv')
        if file_path_name is not None and file_path_name[-4:] != '.csv':
            raise ValueError('Given file path must end with \'.csv\'')

        sp_500 = FinanceDataHelper.get_sp500_tickers()

        combined_df = None
        i = 1
        for ticker in sp_500:
            try:
                new_df = FinanceDataHelper.get_stock_month_data(ticker, most_recent_day=most_recent_day)
                combined_df = new_df if combined_df is None else pd.concat([combined_df, new_df])
            except Exception as e:
                print(e)
            print(i)
            i += 1

        if save_to_csv and combined_df is not None:
            combined_df.to_csv(file_path_name) 

        return combined_df
    
    @staticmethod
    def get_data_from_csv(file_path: str) -> pd.DataFrame:
        df = pd.read_csv(file_path).set_index(["Symbol","Date"])
        return df
    



