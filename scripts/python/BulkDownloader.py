import os
import requests
from pathlib import Path
from datetime import datetime, timedelta
from zipfile import ZipFile

class BulkDownloader():
    def __init__(self, file_format:str):
        self.file_format = file_format
        self.archive_url = "https://data.datalibrary.uk/transport/BODS-ARCHIVE/"
        self.ROOT = Path(__file__).cwd().resolve()
        self.allowed_formats = ['gtfsrt', 'sirivm', 'timetables']
        assert self.file_format in self.allowed_formats

    def create_url_for_given_day(self, daysago) -> os.path:
        self.given_day = (datetime.today() - timedelta(days=daysago)).date()
        self.filename_to_download = f'{self.file_format}-' + self.given_day.strftime("%Y%m%d") + '.zip'

        file_to_download_full_url = os.path.join(self.archive_url + self.file_format + "/", 
                                        str(self.given_day.year), 
                                        str(self.given_day.month).zfill(2), 
                                        str(self.given_day.day).zfill(2),
                                        self.filename_to_download)
        
        print(f"File to download: {file_to_download_full_url}\n")

        return file_to_download_full_url
    
    def create_temporary_directory(self):
        self.TEMPDIR = self.ROOT / "temp"
        self.TEMPDIR.mkdir(exist_ok=True)

        self.dirs = {
            'gtfsrt': self.TEMPDIR / 'gtfsrt',
            'sirivm': self.TEMPDIR / 'sirivm',
            'timetables': self.TEMPDIR / 'timetables'
        }

        self.dirs[self.file_format].mkdir(exist_ok=True)

    def bulk_download(self, url: str) -> Path:
        download_location = self.TEMPDIR / url.split('/')[-1]
        # print("download loc", download_location)
        if Path(download_location).exists():
            print(f"{download_location} already exists in the temporary directory. Skipping download.\n")
        else:
            # NOTE the stream=True parameter below
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(download_location, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)
        
        return download_location
    
    #TODO move this to OperatorPerformance
    def unzip_bulk_download(self, path: Path):
        with ZipFile(path) as zf:
            i = 1
            namelist = zf.namelist()
            total = len(namelist)
            for file in namelist:
                with zf.open(file, 'r') as f:
                    # get the file name
                    file_name = Path(file).name
                    # read the content
                    content = f.read()
                    # write to a new file in the current directory
                    path = self.dirs[self.file_format]
                    with open(path / file_name, 'wb') as out_file:
                        out_file.write(content)
                if i % (total // 10) == 0:
                    print(f"Unzipped {round(i*100 / total)}% of {total} files into {path}")
                i += 1

    def run(self, daysago=1):
        full_download_url = self.create_url_for_given_day(daysago)
        self.create_temporary_directory()
        download_location = self.bulk_download(full_download_url)
        
        #TODO move this to OperatorPerformance
        self.unzip_bulk_download(download_location)

if __name__ == "__main__":
    BulkDownloader(file_format='gtfsrt').run()
    BulkDownloader(file_format='timetables').run()