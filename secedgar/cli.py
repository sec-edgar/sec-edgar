import os
from datetime import datetime

import click

from secedgar.exceptions import FilingTypeError
from secedgar.filings import DailyFilings, Filing, FilingType


@click.group()
@click.option('-u', '--user-agent',
              help='Value used for HTTP header "User-Agent" for all requests.',
              required=True,
              type=str)
@click.pass_context
def cli(ctx, user_agent):
    """Main CLI group."""
    ctx.ensure_object(dict)
    ctx.obj['user_agent'] = user_agent


def date_cleanup(date):
    """Transforms date of form YYYYMMDD to datetime object.

    Args:
        date (Union[str, NoneType]): Date of the form YYYYMMDD to be transformed.

    Returns:
        ``datetime.datetime`` object if given string.
        Returns None if None is given.
    """
    return datetime.strptime(date, "%Y%m%d") if date is not None else None


@cli.command()
@click.option('-l', '--lookups',
              help='Companies and tickers to include in filing download.',
              required=True,
              multiple=True)
@click.option('-t', '--ftype', help="""Choose a filing type.
             See ``secedgar.filings.FilingType`` for a full list of available enums.
             Should be of the form FILING_<filing type>.""",
              required=True)  # Need to convert this to enum somehow
@click.option('-s', '--start',
              help="""Start date for filings.
              Should be in the format YYYYMMDD. Defaults to first available filing.""",
              type=str)
@click.option('-e', '--end',
              help='End date for filings. Should be in the format YYYYMMDD. Defaults to today.',
              type=str)
@click.option('-n', '--count',
              help='Number of filings to save. Defaults to all.',
              type=int)
@click.option('--directory',
              help="""Directory where files will be saved.
              Defaults to directory from which CLI is being executed.""",
              default=os.getcwd(), type=str)
@click.pass_context
def filing(ctx, lookups, ftype, start, end, count, directory):
    """Click command for downloading filings. Run ``secedgar filing --help`` for info."""
    # If given filing type is not valid enum, raise FilingTypeError
    try:
        ftype = FilingType[ftype]
    except KeyError:
        raise FilingTypeError()

    f = Filing(cik_lookup=lookups,
               filing_type=ftype,
               start_date=date_cleanup(start),
               end_date=date_cleanup(end),
               count=count,
               user_agent=ctx.obj['user_agent'])
    f.save(directory=directory)


@cli.command()
@click.option('-d', '--date', help="""Date to look up daily filings for.
              Should be in the format YYYYMMDD.""", required=True, type=str)
@click.option('--directory', help="""Directory where files will be saved.
              Defaults to directory from which CLI is being executed.""",
              default=os.getcwd(), type=str)
@click.pass_context
def daily(ctx, date, directory):
    """Click command for downloading daily filings. Run ``secedgar daily --help`` for info."""
    d = DailyFilings(date=date_cleanup(date), user_agent=ctx.obj['user_agent'])
    d.save(directory=directory)
