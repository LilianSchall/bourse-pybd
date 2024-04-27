import pandas as pd
import numpy as np
import sklearn
import dateutil
import os

import timescaledb_model as tsdb

# db = tsdb.TimescaleStockMarketModel('bourse', 'ricou', 'db', 'monmdp')        # inside docker
db = tsdb.TimescaleStockMarketModel('bourse', 'ricou', 'localhost', 'monmdp') # outside docker
companies_save = None 
comp_batch = None
stock_batch = None

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
        comp_batch = companies
    else:
        comp_batch = pd.concat([comp_batch, companies])

    if stock_batch is None:
        stock_batch = stocks
    else:
        stock_batch = pd.concat([stock_batch, stocks])

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

def store_file(filepath, nb_companies, nb_files_processed):
    filename = os.path.basename(filepath)
    if db.is_file_done(filename):
        print("File has already been processed")
        return
    df = pd.read_pickle(filepath)

    alias, date = compute_alias_date(filename)
    market = convert_generator_to_df(db.df_query(f"SELECT id FROM markets WHERE alias = '{alias}'"))
    df["mid"] = market.iloc[0]["id"]
    df["date"] = date

    nb_companies = process_dataframe(df, nb_companies)
    if nb_files_processed % 100 == 0 and nb_files_processed != 0:
        global comp_batch
        global stock_batch
        print(f"Committing {100} files to db")
        db.df_write(comp_batch, "companies")
        db.df_write(stock_batch, "stocks")
        comp_batch, stock_batch = None, None

    return nb_companies 

def process_files(dir, nb_companies=0, nb_files_processed=0):
    for root, dirs, files in os.walk(dir):
        for file in files:
            nb_companies = store_file(os.path.join(root, file),
                                      nb_companies,
                                      nb_files_processed)
            nb_files_processed += 1
            if nb_files_processed % 10 == 0:
                print(nb_files_processed)
        for dir in dirs:
            nb_files_processed, nb_companies = process_files(dir, nb_companies=0, nb_files_processed=nb_files_processed)
    return nb_files_processed, nb_companies


if __name__ == '__main__':
    process_files("./bourse/")
    print("Done")
