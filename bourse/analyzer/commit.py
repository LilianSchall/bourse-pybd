import os
from datetime import datetime
from itertools import repeat
from multiprocessing import get_context

import pandas as pd
import timescaledb_model as tsdb
from processor import Processor

db = tsdb.TimescaleStockMarketModel("bourse", "ricou", "db", "monmdp")  # inside docker
# db = tsdb.TimescaleStockMarketModel(
#     "bourse", "ricou", "localhost", "monmdp"
# )  # outside docker


class Committer:
    """
        The committer is used to commit processed DataFrame to the database
        efficiently through a processpool.
    """
    @staticmethod
    def commit_companies(df: pd.DataFrame):
        db.df_write(df, "companies")

    @staticmethod
    def commit_stocks(df: pd.DataFrame):
        db.df_write(df, "stocks")

    @staticmethod
    def commit_daystocks(df: pd.DataFrame):
        db.df_write(df, "daystocks")

    def __init__(self, log, pool_size=os.cpu_count()):
        self.pool_size = pool_size
        self.log = log
        self.db = db

    def __convert_generator_to_df(self, gen):
        dflist = []
        for gen in gen:
            dflist.append(gen)
        df = pd.concat(dflist)
        return df

    def get_market(self, alias: str):
        return self.__convert_generator_to_df(
            db.df_query(f"SELECT id FROM markets WHERE alias = '{alias}'")
        )

    def commit_if_needed(
        self, proc: Processor, prev_date: datetime, prev_alias: str, alias: str
    ):
        """
            @param proc: a stock processor
            @param prev_date: the date of the previous file that has been processed
            @param prev_alias: the market alias of the previous file that has been processed
            @param alias: the current market alias to store
        """
        if len(proc.daystocks_batch) == self.pool_size or (
            prev_date is None and alias != prev_alias and prev_alias != ""
        ):
            proc.clean_stocks(self.pool_size)

            self.log.debug(f"Committing {len(proc.stocks_batch)} files to db")
            with get_context("spawn").Pool(self.pool_size) as p:
                self.log.info("..........")
                p.map(Committer.commit_companies, proc.companies_batch)
                self.log.info("===>......")
                p.map(Committer.commit_stocks, proc.stocks_batch)
                self.log.info("======>...")
                p.map(Committer.commit_daystocks, proc.daystocks_batch)
                self.log.info("=========>")
                proc.reset_batch()
