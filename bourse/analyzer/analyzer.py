import os
from datetime import datetime
from multiprocessing import get_context

import dateutil
import numpy as np
import pandas as pd
import sklearn
import timescaledb_model as tsdb
from commit import Committer
from mylogging import getLogger
from processor import Processor

log = getLogger(__name__)
processor = Processor(log)
committer = Committer(log)


def compute_alias_date(filename: str):
    """
        Compute the market alias from the filename 
        along with the date of snapshot
        @param filename: the name of the file to process
    """
    alias = filename.split()[0]
    date_str = filename[:-4].replace(alias + " ", "")
    date: datetime = dateutil.parser.parse(date_str)
    return alias, date


def store_file(filepath, nb_companies, prev_date, prev_alias):
    """
        Process and store a file into the database through a batch process
        @param filepath: the path of the file to process
        @param nb_companies: the number of companies
        @param prev_date: the date of the previous file that has been processed
        @param prev_alias: the market alias of the previous file
                           that has been processed
    """
    filename = os.path.basename(filepath)
    # if db.is_file_done(filename):
    #    log.debug("File has already been processed")
    #    return nb_companies, prev_date, prev_alias
    df = pd.read_pickle(filepath)

    alias, date = compute_alias_date(filename)
    market = committer.get_market(alias)
    df["mid"] = market.iloc[0]["id"]
    df["date"] = date

    if date.date() != prev_date and prev_date is not None:
        processor.process_daystocks(prev_date)

    committer.commit_if_needed(processor, prev_date, prev_alias, alias)
    nb_companies = processor.process_dataframe(df, nb_companies)

    return nb_companies, date.date(), alias


def process_files(dir, nb_companies=0, nb_files_processed=0, previous_alias=""):
    """
        Run through a directory and process all files into the database
        @param dir: the path to the dir to process
        @param nb_companies: the number of companies already processed
        @param nb_files_processed: the number of files already processed
        @param previous_alias: the market alias of the previous file
                               that has been processed
    """
    log.debug(dir)
    # we walk each directory and
    # call recursively this function for each directory
    # if we land on a file, we process this file
    # we process them on the alphabetical ascending order
    # because we'd like to process every file of a trading day
    # (this will be our batch to commit)
    for root, dirs, files in os.walk(dir):
        prev_date = None
        for file in sorted(files):
            nb_companies, prev_date, previous_alias = store_file(
                os.path.join(root, file), nb_companies, prev_date, previous_alias
            )
            nb_files_processed += 1
            if nb_files_processed % 10 == 0:
                log.debug(nb_files_processed)
        for dir in sorted(dirs):
            nb_files_processed, nb_companies = process_files(
                dir, nb_companies=0, nb_files_processed=nb_files_processed
            )
    return nb_files_processed, nb_companies


if __name__ == "__main__":
    process_files("./data/")
    log.debug("Done")
