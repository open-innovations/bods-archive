import argparse
import requests
import re
from pathlib import Path
from bs4 import BeautifulSoup
from time import sleep

class ArchiveDownloader:
    def __init__(self):
        """
        Initializes the downloader by parsing command-line arguments, extracting date ranges,
        and constructing a list of archive URLs to scrape.
        Attributes:
            args: Parsed command-line arguments.
            format (str): Data format specified by the user.
            start_year (int): Start year of the download range.
            start_month (int): Start month of the download range.
            start_day (int): Start day of the download range.
            end_year (int): End year of the download range.
            end_month (int): End month of the download range.
            end_day (int): End day of the download range.
            base_url (str): Base URL for the BODS archive.
            urls (list): List of URLs to download, generated from the date range and format.
            OUTDIR (Path): Output directory for downloaded files.
        Steps:
            1. Parse and store command-line arguments.
            2. Extract and convert start/end dates from arguments.
            3. Generate URLs for each date in the specified range.
            4. Create the output directory if it does not exist.
        """
        
        self.args = self._set_args()

        self.format = self.args.format
        self.start_year, self.start_month, self.start_day = self.args.sd.split("/")
        self.end_year, self.end_month, self.end_day = self.args.ed.split("/")

        self.start_day = int(self.start_day)
        self.start_month = int(self.start_month)
        self.start_year = int(self.start_year)
        self.end_day = int(self.end_day)
        self.end_month = int(self.end_month)
        self.end_year = int(self.end_year)

        self.base_url = "https://data.datalibrary.uk/transport/BODS-ARCHIVE"
        self.urls = []
        
        for y in range(self.start_year, self.end_year + 1):
            for m in range(self.start_month, self.end_month + 1):
                for d in range(self.start_day, self.end_day + 1):
                    # zfill needed to make the correct URL
                    self.urls.append(f"{self.base_url}/{self.format}/{y}/{str(m).zfill(2)}/{str(d).zfill(2)}/")
        
        self.OUTDIR = Path(__file__).cwd() / self.args.outpath
        self.OUTDIR.mkdir(parents=True, exist_ok=True)

    def _set_args(self):
        """
        Parses and returns command-line arguments for the archive downloader script.
        Arguments:
            -s, --sd: Start date as a string in 'YYYY/mm/dd' format.
            -e, --ed: End date as a string in 'YYYY/mm/dd' format.
            -f, --format: Data format, either 'gtfsrt' or 'sirivm'.
            -o, --outpath: Output path to store downloads, relative to the current working directory.
        Returns:
            argparse.Namespace: Parsed command-line arguments.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--sd", default='2025/07/01', help="Date string format 'YYYY/mm/dd'")
        parser.add_argument("-e", "--ed", default='2025/07/01', help="Date string format 'YYYY/mm/dd'")
        parser.add_argument("-f", "--format", default='gtfsrt', help='Either "gtfsrt" or "sirivm"')
        parser.add_argument("-o", "--outpath", default='data', help="Output path to store downloads. Relative to current working directory.")
        args = parser.parse_args()
        return args
    
    def _fail_with_exception(self, e):
        print(f"Failed with exception: {e}")

    def _links_from_url(self, url):
        """
        Fetches all links from the given URL, filters for GTFS-RT/SIRI zip files matching a specific pattern,
        and downloads them to the output directory, respecting a rate limit of 1 request per second.
        
        Args:
            url (str): The URL of the webpage to scrape for GTFS-RT zip file links.
        Side Effects:
            - Downloads matching zip files to self.OUTDIR.
            - Prints status messages for each link processed.
            - Sleeps for just over 1 second between requests to respect rate limits.
        Notes:
            - Only files with names matching the pattern 'gtfsrt-YYYYMMDDTHHMMSS.zip' are downloaded.
            - Non-matching links are skipped with a printed message.
        """
        # Try to get the content of a given archive page.
        try:
            page_content = requests.get(url)
        except Exception as e:
            self._fail_with_exception(e)
        
        # Try to parse the archive page, grab the links to files, then get the files themselves.
        try:
            text_content = page_content.text

            soup = BeautifulSoup(text_content, "html.parser")
        
            for atag in soup.find_all('a'):
                href = atag.get("href")
                href_str = str(href)
                if not href_str.endswith(".zip"):
                    # If its not a zip file.
                    print(f"'{href}'", "is not a zip file.")
                    
                elif re.match(re.escape(self.format) + r"-[0-9]{8}T[0-9]{6}.zip", str(href)): # File name must be of form format-yyyymmddTHHMMSS.zip
                    
                    full_filepath = url + href # Build the full path for the GET request

                    print("Downloading:", href, "\n")

                    response = requests.get(full_filepath)
                    
                    if response.ok:
                        # Save the file
                        with open(self.OUTDIR / href, mode="wb") as file:
                            file.write(response.content)
                    else:
                        print(f"Reponse not ok. Status code: {response.status_code}")

                else:
                    print(f"'{href}'", "is a zip file but not of the right name format. Skipping...\n")
                
                # Add this to ensure we obey the rate limit of 1req/s
                sleep(1.05)
            
        except Exception as e:
            self._fail_with_exception(e)

    def run(self):
        for url in self.urls:
            try:
                print(f"Downloading data for {url}\n")
                self._links_from_url(url)
            except Exception as e:
                self._fail_with_exception(e)


if __name__ == "__main__":
    ArchiveDownloader().run()