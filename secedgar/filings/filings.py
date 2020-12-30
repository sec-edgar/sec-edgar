from filings import DailyFilings, MasterFilings, CompanyFilings
def Filings(date, end_date=None, companies=None, filing_types=None, result_filter_fn=None, maximum_results=None):
        if companies is None:
            if end_date is None:
                return DailyFilings()

            return MasterFilings()
        return CompanyFilings()

"""
class FilingEngine:

    client = NetworkClient()

    ''' save the text files from each result '''
    def save_text_files(directory, dir_pattern=None, file_pattern=None):
        self.engine.save_text_files(**kwargs)
    '''save documents in index filings matching criterion. First requests index for file list.'''
    def save_documents(directory, dir_pattern=None, file_pattern=None, filter_fn=None):
        pass
    ''' get document list in index filings matching criterion. '''
    def get_documents(filter_fn=None, as_iterator=False):
        pass
    ''' download the results as a tsv. If results are not a tsv / from an index list, convert to a tsv. '''
    def save_results(file_name):
        pass
    ''' return a list of the results.'''
    def get_results(as_iterator=True):
        pass
"""