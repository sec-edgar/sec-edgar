import click
from datetime import datetime
import os
from secedgar.filings import Filing, DailyFilings


@click.group()
def cli():
    pass


def date_cleanup(date):
    """Transforms date of form YYYYMMDD to datetime object.

    Args:
        date (str): Date of the form YYYYMMDD to be transformed.

    Returns:
        ``datetime.datetime`` object.
    """
    return datetime.strptime(date, "%Y%m%d")


@cli.command()
@click.option('-l', '--lookups', help='Companies and tickers to include in filing download.', required=True)
@click.option('-t', '--ftype', help='Choose a filing type.')  # Need to convert this to enum somehow
@click.option('-s', '--start', help='Start date for filings. Should be in the format YYYYMMDD. Defaults to first available filing.', type=str)
@click.option('-e', '--end', help='End date for filings. Should be in the format YYYYMMDD. Defaults to today.', type=str)
@click.option('-n', '--count', help='Number of filings to save. Defaults to all.', type=int)
@click.option('--directory', help='Directory where files will be saved. Defaults to directory from which CLI is being executed.', default=os.getcwd(), type=str)
def filing(lookups, ftype, start, end, count, directory):
    f = Filing(cik_lookup=lookups,
               filing_type=ftype,
               start_date=date_cleanup(start),
               end_date=date_cleanup(end),
               count=count)
    f.save(directory=directory)


@cli.command()
@click.option('-d', '--date', help='Date to look up daily filings for. Should be in the format YYYYMMDD.', required=True, type=str)
@click.option('--directory', help='Directory where files will be saved. Defaults to directory from which CLI is being executed.', default=os.getcwd(), type=str)
def daily(date, directory):
    d = DailyFilings(date=date_cleanup(date))
    d.save(directory=directory)
