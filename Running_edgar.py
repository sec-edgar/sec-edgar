from secedgar.filings import Filing, FilingType

'#"'$_10Q filings for Apple (ticker "aapl")
my_filings = Filing(cik_lookup='aapl', filing_type=FilingType.FILING_10Q)
my_filings.save('~/path/to/dir')
