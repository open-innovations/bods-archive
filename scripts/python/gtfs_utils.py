import pandas as pd
from zipfile import ZipFile

class GTFSTimetable:
    '''
    Load a GTFS zip file into a class for easy manipulation.
    
    Attributes
    ----------
    files: list
        a list of files in the Zip file.
    dfs: dict     
        a dictionary of pandas.DataFrame (s) where the key is the name of the file and the value is the dataframe.
    '''
    def __init__(self, path:str, file_type=".txt"):
        if path.endswith(".zip"):
            with ZipFile(path) as zf:
                # create a dictionary containing the data as dataframes
                # indexed by the filename (extension removed)
                self.dfs = {text_file.filename.replace(file_type, ""): pd.read_csv(zf.open(text_file.filename))
                            for text_file in zf.infolist()
                            if text_file.filename.endswith(file_type)}
                
                # add a list of files
                self.files = zf.namelist()
