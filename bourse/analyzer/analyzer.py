import pandas as pd
import dateutil
import os
from multiprocessing import get_context

import timescaledb_model as tsdb
from mylogging import getLogger
from processor import Processor
from commit import Committer

from datetime import datetime

log = getLogger(__name__)
processor = Processor(log)
committer = Committer(log)


def compute_alias_date(filename: str):
        alias = filename.split()[0]
        date_str = filename[:-4].replace(alias + " ", "")
        date: datetime = dateutil.parser.parse(date_str)
        return alias, date


def store_file(filepath, nb_companies, prev_date, prev_alias):
    filename = os.path.basename(filepath)
    #if db.is_file_done(filename):
    #    log.debug("File has already been processed")
    #    return nb_companies, prev_date, prev_alias
    df = pd.read_pickle(filepath)

    alias, date = compute_alias_date(filename)
    market = committer.get_market(alias)
    df["mid"] = market.iloc[0]["id"]
    df["date"] = date
    
    if date.date() != prev_date and prev_date != None:
        processor.process_daystocks(prev_date)

    committer.commit_if_needed(processor, prev_date, prev_alias, alias)
    nb_companies = processor.process_dataframe(df, nb_companies)

    return nb_companies, date.date(), alias

def process_files(dir, nb_companies=0, nb_files_processed=0, previous_alias=""):
    log.debug(dir)
    for root, dirs, files in os.walk(dir):
        prev_date = None
        for file in sorted(files):
            nb_companies, prev_date, previous_alias = store_file(
                os.path.join(root, file),
                nb_companies,
                prev_date,
                previous_alias
            )
            nb_files_processed += 1
            if nb_files_processed % 10 == 0:
                log.debug(nb_files_processed)
        for dir in sorted(dirs):
            nb_files_processed, nb_companies = process_files(dir, nb_companies=0, nb_files_processed=nb_files_processed)
    return nb_files_processed, nb_companies


if __name__ == '__main__':
    process_files("./data/")
    log.debug("Done")
