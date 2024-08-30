import pandas as pd
from FinanceDataHelper import FinanceDataHelper

class FinanceData(object):
    @staticmethod
    def get_data(save_to_csv: bool = True, file_path_name: str | None = None, most_recent_day: bool = True) -> pd.DataFrame:
        """
        Gets data data from S&P 500 for about the past month through Yahoo Finance API

        Args:
            save_to_csv: if you want the data to also be saved as a csv -> bool
            file_path_name: the relative path and file name (only needed if save_to_csv is true) -> str
            most_recent_day: if you want data from the most recent day in order to make predictions -> bool

        Returns:
            The resulting Pandas DataFrame with S&P 500 data for about the past month -> pandas.DataFrame
        """
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

        return combined_df #type: ignore
    
    @staticmethod
    def get_data_from_csv(file_path_name: str) -> pd.DataFrame:
        """
        Gets data data from S&P 500 for about the past month from a saved .csv file

        Args:
            file_path_name: the relative path and file name of the saved .csv file-> str

        Returns:
            The resulting Pandas DataFrame with S&P 500 data for about the past month -> pandas.DataFrame
        """
        df = pd.read_csv(file_path_name).set_index(["Symbol","Date"])
        return df
    



