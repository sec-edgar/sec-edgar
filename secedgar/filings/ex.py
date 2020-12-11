from edgar import search


engine = search(quarter=3, year=2020, type='4', use_tar=True)
engine.save_raw()
engine.save_formatted()