import numpy as np
import pandas as pd


class Processor:
    """
        The Processor is used to load dataframes from files and
        process, clean and compress them.
    """
    def __init__(self, log):
        self.stocks_batch = []
        self.day_batch = []
        self.daystocks_batch = []
        self.companies_batch = []
        self.companies_save: None | pd.DataFrame = None
        self.log = log

    def __process_companies(self, df: pd.DataFrame | pd.Series, nb_companies: int):
        """
            Process the dataframe and fill up the company table.
            @param df: the dataframe to process
            @param nb_companies: the number of companies processed
        """
        df.drop("symbol", axis=1, inplace=True)
        df.dropna(inplace=True)

        companies = (
            df.reset_index()
            .drop_duplicates("symbol")
            .drop(columns=["last", "volume", "date"])
            .reset_index(drop=True)
        )
        companies.index.rename("id", inplace=True)

        if self.companies_save is None:
            self.companies_save = companies
            return companies, nb_companies + len(companies)
        else:
            # detecting new companies
            mask = companies.symbol.isin(self.companies_save.symbol)
            new_companies = companies[~mask].copy()
            new_companies.reset_index(drop=True, inplace=True)
            new_companies.index.rename("id", inplace=True)
            new_companies.index += nb_companies

            # saving new companies
            self.companies_save = pd.concat([self.companies_save, new_companies])
            # db.df_write(new_companies, "companies")
            # return updated list of companies
            return new_companies, nb_companies + len(new_companies)

    def __process_stocks(self, df: pd.DataFrame | pd.Series):
        """
            Process the dataframe and fill up the stocks table.
            @param df: the dataframe to process
        """
        stocks = df.reset_index().merge(
            self.companies_save.assign(cid=self.companies_save.index)[
                ["symbol", "cid"]
            ],
            on="symbol",
            how="left",
        )
        stocks.set_index("cid", inplace=True)
        stocks = stocks.drop(columns=["symbol", "name", "mid"])

        stocks["value"] = stocks["last"].astype(str)
        stocks.drop(axis=1, labels="last", inplace=True)

        stocks["value"] = stocks["value"].str.replace("\([a-zA-Z]\)| ", "", regex=True)
        stocks["value"] = stocks["value"].astype(float)
        return stocks

    def process_dataframe(self, df: pd.DataFrame | pd.Series, nb_companies: int):
        """
            Process the dataframe of a file by extracting its data and put it
            in the company and stocks table.
            @param df: the dataframe to process
            @param nb_companies: the number of companies processed
        """
        # companies, stocks, daystocks, file_done, tags
        companies, nb_companies = self.__process_companies(df, nb_companies)
        stocks = self.__process_stocks(df)

        self.companies_batch.append(companies)
        self.stocks_batch.append(stocks)
        self.day_batch.append(stocks)

        return nb_companies

    def process_daystocks(self, prev_date):
        """
            From the processed stocks batch, create a daystock out of it
            @param prev_date: the date of the previous file processed.
        """
        self.log.debug(f"Group by {len(self.day_batch)} for daystocks")
        daystocks = pd.concat(self.day_batch, ignore_index=False)
        daystocks = daystocks.groupby(["cid"]).agg(
            date=pd.NamedAgg(column="value", aggfunc="first"),
            open=pd.NamedAgg(column="value", aggfunc="first"),
            close=pd.NamedAgg(column="value", aggfunc="last"),
            high=pd.NamedAgg(column="value", aggfunc="max"),
            low=pd.NamedAgg(column="value", aggfunc="min"),
            # volume=pd.NamedAgg(column='volume', aggfunc='sum'),
        )
        daystocks["date"] = prev_date
        self.daystocks_batch.append(daystocks)
        self.day_batch = []

    def reset_batch(self):
        self.stocks_batch = []
        self.companies_batch = []
        self.daystocks_batch = []

    def clean_stocks(self, pool_size):
        """
            Clean the stock batch by removing repeating stock values, so that
            we store fewer value in database.
        """
        stocks = pd.concat(self.stocks_batch, ignore_index=False)

        stocks.reset_index(inplace=True)
        stocks.sort_values(["cid", "date"], inplace=True)

        stocks["day"] = stocks["date"].dt.date

        selected_columns = ["cid", "volume", "value", "day"]
        df1 = stocks[
            stocks[selected_columns]
                .ne(stocks[selected_columns]
                .shift(1)).any(axis=1)
        ]
        df2 = stocks[
            stocks[selected_columns].ne(stocks[selected_columns].shift(-1)).any(axis=1)
        ]
        stocks = pd.concat([df1, df2.loc[~df2.index.isin(df1.index)]])

        stocks.set_index("cid", drop=True, inplace=True)
        stocks.drop(columns="day", inplace=True)

        self.stocks_batch = np.array_split(stocks, pool_size)
