import pandas as pd
import numpy as np
import sklearn
import dateutil
import os
from multiprocessing import get_context

import timescaledb_model as tsdb
from mylogging import getLogger

# db = tsdb.TimescaleStockMarketModel('bourse', 'ricou', 'db', 'monmdp')        # inside docker
db = tsdb.TimescaleStockMarketModel('bourse', 'ricou', 'localhost', 'monmdp') # outside docker
companies_save = None 
comp_batch = None
stock_batch = None

log = getLogger(__name__)

def process_companies(df: pd.DataFrame | pd.Series, nb_companies: int):
    global companies_save
    df.drop("symbol", axis=1, inplace=True)
    df.dropna(inplace=True)

    companies = df.reset_index()\
        .drop_duplicates("symbol")\
        .drop(columns=["last", "volume", "date"])\
        .reset_index(drop=True)
    companies.index.rename("id", inplace=True)

    if companies_save is None:
        companies_save = companies
        return companies, nb_companies + len(companies)
    else:
        # detecting new companies
        mask = companies.symbol.isin(companies_save.symbol)
        new_companies = companies[~mask].copy()
        new_companies.reset_index(drop=True, inplace=True)
        new_companies.index.rename("id", inplace=True)
        new_companies.index += nb_companies

        # saving new companies
        companies_save = pd.concat([companies_save, new_companies])
        # db.df_write(new_companies, "companies")
        # return updated list of companies
        return new_companies, nb_companies + len(new_companies)

def process_stocks(df: pd.DataFrame | pd.Series):
    stocks = df.reset_index()\
        .merge(companies_save
               .assign(cid=companies_save.index)[[ "symbol", "cid" ]],
               on="symbol", how="left")
    stocks.set_index("cid", inplace=True)
    stocks = stocks.drop(columns=["symbol", "name", "mid"])

    stocks["value"] = stocks["last"].astype(str)
    stocks.drop(axis=1, labels="last", inplace=True)

    stocks["value"] = stocks["value"]\
        .str.replace("\([a-zA-Z]\)| ", "", regex=True) 
    stocks["value"] = stocks["value"].astype(float)
    # db.df_write(stocks, "stocks")
    return stocks

def concat_df(companies, stocks):
    global comp_batch
    global stock_batch

    if comp_batch is None:
        comp_batch = [companies]
        # comp_batch = companies
    else:
        #comp_batch = pd.concat([comp_batch, companies])
        comp_batch.append(companies)

    if stock_batch is None:
        stock_batch = [stocks]
    else:
        # stock_batch = pd.concat([stock_batch, stocks])
        stock_batch.append(stocks)

def process_dataframe(df: pd.DataFrame | pd.Series, nb_companies: int):
    # companies, stocks, daystocks, file_done, tags
    companies, nb_companies = process_companies(df, nb_companies)
    stocks = process_stocks(df)

    concat_df(companies, stocks)

    return nb_companies

def convert_generator_to_df(gen):
        dflist = []
        for gen in gen:
            dflist.append(gen)
        df = pd.concat(dflist)
        return df

def compute_alias_date(filename: str):
        alias = filename.split()[0]
        date_str = filename[:-4].replace(alias + " ", "")
        date = dateutil.parser.parse(date_str)
        return alias, date

def commit_companies(df):
    db.df_write(df, "companies")

def commit_stocks(df):
    db.df_write(df, "stocks")

def commit_daystocks(df):
    db.df_write(df, "daystocks")

def store_file(filepath, nb_companies, nb_files_processed, prev_date):
    filename = os.path.basename(filepath)
    if db.is_file_done(filename):
        log.debug("File has already been processed")
        return
    df = pd.read_pickle(filepath)

    alias, date = compute_alias_date(filename)
    market = convert_generator_to_df(db.df_query(f"SELECT id FROM markets WHERE alias = '{alias}'"))
    df["mid"] = market.iloc[0]["id"]
    df["date"] = date
    
    #if nb_files_processed % 100 == 0 and nb_files_processed != 0:
    if date.date() != prev_date and prev_date != None:
        global comp_batch
        global stock_batch
        log.debug(f"Committing {len(stock_batch)} files to db")
        #db.df_write(comp_batch, "companies")
        #db.df_write(stock_batch, "stocks")
        daystocks = pd.concat(stock_batch, ignore_index=False)
        daystocks = daystocks.groupby(['cid']).agg(date=pd.NamedAgg(column='value', aggfunc='first'),
                                                   open=pd.NamedAgg(column='value', aggfunc='first'),
                                                   close=pd.NamedAgg(column='value', aggfunc='last'),
                                                   high=pd.NamedAgg(column='value', aggfunc='max'),
                                                   low=pd.NamedAgg(column='value', aggfunc='min'),
                                                   #volume=pd.NamedAgg(column='volume', aggfunc='sum'),
        )
        daystocks['date'] = prev_date

        with get_context("spawn").Pool(12) as p:
            p.map(commit_companies, comp_batch)
            p.map(commit_stocks, stock_batch)
            p.map(commit_daystocks, np.array_split(daystocks, 12))

        comp_batch, stock_batch = None, None

    nb_companies = process_dataframe(df, nb_companies)


    return nb_companies, date.date()

def process_files(dir, nb_companies=0, nb_files_processed=0):
    log.debug(dir)
    for root, dirs, files in os.walk(dir):
        prev_date = None
        for file in sorted(files):
            nb_companies, prev_date = store_file(os.path.join(root, file),
                                      nb_companies,
                                      nb_files_processed, prev_date)
            nb_files_processed += 1
            if nb_files_processed % 10 == 0:
                log.debug(nb_files_processed)
        for dir in sorted(dirs):
            nb_files_processed, nb_companies = process_files(dir, nb_companies=0, nb_files_processed=nb_files_processed)
    return nb_files_processed, nb_companies


if __name__ == '__main__':
    process_files("./data/")
    log.debug("Done")
